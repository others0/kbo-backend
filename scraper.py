import requests
from datetime import datetime, timedelta, timezone
import time
from cachetools import TTLCache
from playwright.sync_api import sync_playwright
import re
from bs4 import BeautifulSoup

KBO_TEAM_CODES = {
    "삼성": "SS", "키움": "WO", "두산": "OB", "SSG": "SK", 
    "롯데": "LT", "LG": "LG", "KIA": "HT", "한화": "HH", 
    "NC": "NC", "KT": "KT"
}

BASE = "https://api-gw.sports.naver.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
PLAYWRIGHT_CACHE = TTLCache(maxsize=10, ttl=600)

# Team Name -> (Stadium Name, Lat, Lon, isDome)
STADIUMS = {
    "삼성": ("대구", 35.8411, 128.6811, False),
    "LG": ("잠실", 37.5122, 127.0719, False),
    "두산": ("잠실", 37.5122, 127.0719, False),
    "KIA": ("광주", 35.1681, 126.8848, False),
    "롯데": ("사직", 35.1944, 129.0617, False),
    "SSG": ("문학", 37.4370, 126.6933, False),
    "NC": ("창원", 35.2222, 128.5822, False),
    "KT": ("수원", 37.2997, 127.0097, False),
    "한화": ("대전", 36.3171, 127.4292, False),
    "키움": ("고척", 37.4982, 126.8670, True)
}

WEATHER_CACHE = {} # (lat, lon) -> { timestamp, data_dict }
CACHE_TTL = 600 # 10분 캐싱

def get_weather_forecast(lat, lon):
    cache_key = (lat, lon)
    now = time.time()
    
    if cache_key in WEATHER_CACHE:
        cached_time, cached_data = WEATHER_CACHE[cache_key]
        if now - cached_time < CACHE_TTL:
            return cached_data
            
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_probability_max&timezone=Asia/Seoul"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            daily_times = data.get('daily', {}).get('time', [])
            probs = data.get('daily', {}).get('precipitation_probability_max', [])
            
            forecast_dict = {}
            for t, p in zip(daily_times, probs):
                forecast_dict[t] = p
                
            WEATHER_CACHE[cache_key] = (now, forecast_dict)
            return forecast_dict
    except Exception as e:
        print(f"Weather Fetch Error: {e}")
    return {}

API_CACHE = TTLCache(maxsize=100, ttl=30) # 30초 캐싱 (실전 환경에서 밴(Ban) 방지)

def get_json(path):
    url = f"{BASE}{path}"
    headers = {"User-Agent": UA}
    
    # 캐시 확인
    if url in API_CACHE:
        return API_CACHE[url]
        
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get('success'):
                result = data.get('result', {})
                API_CACHE[url] = result # 성공한 응답만 캐싱
                return result
    except Exception as e:
        print(f"[API ERROR] Scrape error for {url}: {e}")
        # 오류 발생 시 이전 캐시된 데이터가 만료되었더라도 반환할 수 있다면 좋겠지만, 
        # TTLCache는 만료되면 지워집니다. 여기서는 빈 딕셔너리로 Fallback 처리합니다.
    return {}

def fetch_standings():
    current_year = datetime.now(timezone(timedelta(hours=9))).year
    data = get_json(f'/statistics/categories/kbo/seasons/{current_year}/teams')
    teams = data.get('seasonTeamStats', [])
    standings = []
    for t in teams[:10]:
        game_behind = t.get('gameBehind', 0.0)
        standings.append({
            "rank": str(t.get('ranking', 0)),
            "team": t.get('teamName', ''),
            "record": f"{t.get('winGameCount', 0)}-{t.get('drawnGameCount', 0)}-{t.get('loseGameCount', 0)}",
            "gameBehind": str(game_behind) if game_behind > 0 else "-",
            "winRate": f"{float(t.get('wra', 0)):.3f}"
        })
    return standings

def scrape_kbo_month(year, month):
    cache_key = f"{year}-{month}"
    if cache_key in PLAYWRIGHT_CACHE:
        return PLAYWRIGHT_CACHE[cache_key]
        
    games = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.koreabaseball.com/Schedule/Schedule.aspx")
            page.select_option("#ddlYear", year)
            page.wait_for_timeout(1000)
            page.select_option("#ddlMonth", month)
            page.wait_for_timeout(2000)
            
            rows = page.query_selector_all("#tblScheduleList > tbody > tr")
            
            current_date = ""
            for row in rows:
                cols = row.query_selector_all("td")
                if len(cols) < 3:
                    continue
                    
                texts = [c.inner_text().strip() for c in cols]
                if len(texts) == 9:
                    current_date = texts[0] # "06.12(수)"
                    time_str = texts[1]
                    match_str = texts[2]
                    location = texts[7]
                    note = texts[8]
                else:
                    time_str = texts[0]
                    match_str = texts[1]
                    location = texts[6]
                    note = texts[7]
                    
                # match_str 파싱: "NC6vs2한화", "SSGvs롯데", "KIA0vs0두산"
                m = re.match(r"([A-Za-z가-힣]+)(\d*)vs(\d*)([A-Za-z가-힣]+)", match_str)
                if m:
                    awayTeam = m.group(1)
                    awayScoreStr = m.group(2)
                    homeScoreStr = m.group(3)
                    homeTeam = m.group(4)
                    
                    status = "BEFORE"
                    awayScore = 0
                    homeScore = 0
                    
                    if awayScoreStr and homeScoreStr:
                        awayScore = int(awayScoreStr)
                        homeScore = int(homeScoreStr)
                        status = "RESULT"
                    
                    if note == "우천취소":
                        status = "CANCEL"
                        
                    games.append({
                        "date_str": current_date,
                        "time": time_str,
                        "awayTeam": awayTeam,
                        "awayScore": awayScore,
                        "homeTeam": homeTeam,
                        "homeScore": homeScore,
                        "location": location,
                        "status": status,
                        "note": note
                    })
            browser.close()
        PLAYWRIGHT_CACHE[cache_key] = games
    except Exception as e:
        print(f"Playwright error: {e}")
    return games

def scrape_live_text(gameId, year_str):
    url = f"https://www.koreabaseball.com/Game/LiveText.aspx?leagueId=1&seriesId=0&gameId={gameId}&gyear={year_str}"
    
    result = {
        "inning": "경기 중",
        "currentBatter": "-",
        "currentPitcher": "-",
        "outs": 0, "strikes": 0, "balls": 0,
        "base1": False, "base2": False, "base3": False,
        "winPitcher": "-", "losePitcher": "-", "savePitcher": "-", "holdPitchers": []
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_timeout(2000) # Give it 2 secs to load text relay
            
            html = page.content()
            browser.close()
            
        soup = BeautifulSoup(html, "html.parser")
        
        # 1. Inning
        inning_strong = soup.select_one(".economy .base strong")
        if inning_strong:
            result["inning"] = inning_strong.text.strip()
            
        # 2. S B O
        result["balls"] = len(soup.select(".sbo .b ul li.on"))
        result["strikes"] = len(soup.select(".sbo .s ul li.on"))
        result["outs"] = len(soup.select(".sbo .o ul li.on"))
        
        # 3. Bases
        bases_img = soup.select_one("#imgThisGameBase")
        if bases_img:
            alt_text = bases_img.get("alt", "")
            result["base1"] = "1" in alt_text
            result["base2"] = "2" in alt_text
            result["base3"] = "3" in alt_text
            
        # 4. Batter / Pitcher
        who = soup.select_one(".who")
        if who:
            result["currentBatter"] = who.text.strip().replace('\n', ' ')
            
        pitcher = soup.select_one(".playerName li.pitcher")
        if pitcher:
            result["currentPitcher"] = pitcher.text.strip()
            
        # 5. Result Pitchers
        for span in soup.find_all("span", class_="red"):
            text = span.text.strip()
            if "승리투수:" in text:
                result["winPitcher"] = text.replace("승리투수:", "").strip()
            elif "패전투수:" in text:
                result["losePitcher"] = text.replace("패전투수:", "").strip()
            elif "세이브투수:" in text:
                result["savePitcher"] = text.replace("세이브투수:", "").strip()
            elif "홀드투수:" in text:
                hold_pitcher = text.split(":")[-1].strip()
                if hold_pitcher not in result["holdPitchers"]:
                    result["holdPitchers"].append(hold_pitcher)
            
    except Exception as e:
        print(f"LiveText Scrape Error: {e}")
        
    return result

def fetch_weekly_schedule(target_team="삼성"):
    today = datetime.now(timezone(timedelta(hours=9)))
    start_of_week = today - timedelta(days=today.weekday()) # Monday
    
    # 해당 월의 모든 경기 가져오기
    year_str = start_of_week.strftime("%Y")
    month_str = start_of_week.strftime("%m")
    all_games = scrape_kbo_month(year_str, month_str)
    
    weekly_games = []
    for i in range(1, 7): # Tuesday to Sunday
        target_date = start_of_week + timedelta(days=i)
        mm_dd = target_date.strftime("%m.%d") # "06.12"
        day_str = ["월", "화", "수", "목", "금", "토", "일"][target_date.weekday()]
        
        # 오늘보다 과거인가?
        is_past = target_date.date() < today.date()
        
        # 이번 주 해당 날짜의 대상 팀 경기 찾기
        target_game = None
        for g in all_games:
            if g['date_str'].startswith(mm_dd):
                if g['homeTeam'] == target_team or g['awayTeam'] == target_team:
                    target_game = g
                    break
        
        if target_game:
            is_home = target_game['homeTeam'] == target_team
            opponent = target_game['awayTeam'] if is_home else target_game['homeTeam']
            location = target_game['location']
            status = target_game['status']
            
            # 과거 날짜인데 BEFORE라면 RESULT로 강제 변환 (크롤링 한계 보정)
            if is_past and status == "BEFORE":
                status = "RESULT"
                
            # 날씨 정보 
            stadium_info = STADIUMS.get(target_game['homeTeam'], ("구장", 37.5665, 126.9780, False))
            lat, lon, is_dome = stadium_info[1], stadium_info[2], stadium_info[3]
            
            if is_dome:
                rain_prob = 0.0
            else:
                forecast = get_weather_forecast(lat, lon)
                date_full = target_date.strftime("%Y-%m-%d")
                prob_percent = forecast.get(date_full, 0)
                rain_prob = prob_percent / 100.0

            weekly_games.append({
                "date": day_str,
                "opponent": opponent,
                "location": location,
                "isHome": is_home,
                "rainProb": rain_prob,
                "status": status,
                "homeScore": target_game['homeScore'],
                "awayScore": target_game['awayScore']
            })
        else:
            # 경기가 없는 경우
            weekly_games.append({
                "date": day_str,
                "opponent": "-",
                "location": "-",
                "isHome": False,
                "rainProb": 0.0,
                "status": "REST",
                "homeScore": 0,
                "awayScore": 0
            })
            
    return weekly_games

def fetch_recent_game(target_team="삼성"):
    today = datetime.now(timezone(timedelta(hours=9)))
    
    # 최근 7일 내의 경기를 탐색 (오늘부터 과거로)
    for i in range(0, 7):
        target_date = today - timedelta(days=i)
        year_str = target_date.strftime("%Y")
        month_str = target_date.strftime("%m")
        mm_dd = target_date.strftime("%m.%d")
        
        all_games = scrape_kbo_month(year_str, month_str)
        target_game = None
        for g in all_games:
            if g['date_str'].startswith(mm_dd):
                if g['homeTeam'] == target_team or g['awayTeam'] == target_team:
                    target_game = g
                    break
                    
        if target_game:
            status = target_game['status']
            # 오늘인데 BEFORE면 킵하고 계속 과거를 찾음? 아니면 그냥 반환?
            # 오늘 경기가 진행 전(BEFORE)이라면, 어제 경기가 있는지 확인하는 로직
            if i == 0 and status == "BEFORE":
                # 오늘 경기는 예정되어 있지만 아직 안했으므로 어제 경기를 찾으러 계속 루프
                continue
                
            is_home = target_game['homeTeam'] == target_team
            
            away_code = KBO_TEAM_CODES.get(target_game['awayTeam'], "SS")
            home_code = KBO_TEAM_CODES.get(target_game['homeTeam'], "SS")
            game_id = f"{year_str}{month_str}{target_date.strftime('%d')}{away_code}{home_code}0"
            
            live_data = {
                "inning": "경기 종료" if status == "RESULT" else ("경기 중" if status == "STARTED" else "경기 전"),
                "currentBatter": "-",
                "batterAverage": "-",
                "currentPitcher": "-",
                "pitcherERA": "-",
                "pitchCount": 0,
                "outs": 0, "strikes": 0, "balls": 0,
                "base1": False, "base2": False, "base3": False,
                "winPitcher": "-", "losePitcher": "-", "savePitcher": "-", "holdPitchers": []
            }
            
            if status in ["STARTED", "RESULT"]:
                scraped_live = scrape_live_text(game_id, year_str)
                live_data.update(scraped_live)
            
            return {
                "gameId": game_id,
                "homeTeam": target_game['homeTeam'],
                "awayTeam": target_game['awayTeam'],
                "homeScore": target_game['homeScore'],
                "awayScore": target_game['awayScore'],
                "status": status,
                "inning": live_data["inning"],
                "currentBatter": live_data["currentBatter"],
                "batterAverage": live_data["batterAverage"],
                "currentPitcher": live_data["currentPitcher"],
                "pitcherERA": live_data["pitcherERA"],
                "pitchCount": live_data["pitchCount"],
                "outs": live_data["outs"],
                "strikes": live_data["strikes"],
                "balls": live_data["balls"],
                "base1": live_data["base1"],
                "base2": live_data["base2"],
                "base3": live_data["base3"],
                "winPitcher": live_data["winPitcher"],
                "losePitcher": live_data["losePitcher"],
                "savePitcher": live_data["savePitcher"],
                "holdPitchers": live_data.get("holdPitchers", [])
            }
            
    # 못 찾은 경우
    return {
        "gameId": f"{today.strftime('%Y%m%d')}SAMSUNG0",
        "homeTeam": "삼성",
        "awayTeam": "휴식",
        "homeScore": 0,
        "awayScore": 0,
        "status": "REST",
        "inning": "경기 전",
        "currentBatter": "-", "batterAverage": "-",
        "currentPitcher": "-", "pitcherERA": "-",
        "pitchCount": 0, "outs": 0, "strikes": 0, "balls": 0,
        "base1": False, "base2": False, "base3": False,
        "winPitcher": "-", "losePitcher": "-", "savePitcher": "-"
    }

def update_mock_data():
    recent_game = fetch_recent_game("삼성")
    weekly_schedule = fetch_weekly_schedule("삼성")
    standings = fetch_standings()
    
    return {
        "recentGame": recent_game,
        "weeklySchedule": weekly_schedule,
        "standings": standings
    }
