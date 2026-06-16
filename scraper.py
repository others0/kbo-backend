import requests
from datetime import datetime, timedelta
import time

BASE = "https://api-gw.sports.naver.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"

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
CACHE_TTL = 3600 # 1시간 캐싱

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

def get_json(path):
    url = f"{BASE}{path}"
    headers = {"User-Agent": UA}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get('success'):
                return data.get('result', {})
    except Exception as e:
        print(f"Scrape error: {e}")
    return {}

def fetch_standings():
    current_year = datetime.now().year
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

def fetch_weekly_schedule(target_team="삼성"):
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday()) # Monday
    
    weekly_games = []
    for i in range(0, 7): # Monday to Sunday
        target_date = start_of_week + timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")
        day_str = ["월", "화", "수", "목", "금", "토", "일"][target_date.weekday()]
        
        data = get_json(f'/schedule/games?upperCategoryId=kbaseball&date={date_str}')
        games = data.get('games', [])
        
        found = False
        for g in games:
            home_name = g.get('homeTeamName')
            away_name = g.get('awayTeamName')
            
            if g.get('categoryId') == 'kbo' and (home_name == target_team or away_name == target_team):
                is_home = home_name == target_team
                opponent = away_name if is_home else home_name
                
                # 구장 및 날씨 로직
                stadium_info = STADIUMS.get(home_name, ("구장", 37.5665, 126.9780, False))
                location = stadium_info[0]
                lat = stadium_info[1]
                lon = stadium_info[2]
                is_dome = stadium_info[3]
                
                if is_dome:
                    rain_prob = 0.0
                    location = "고척돔"
                else:
                    forecast = get_weather_forecast(lat, lon)
                    prob_percent = forecast.get(date_str, 0)
                    rain_prob = prob_percent / 100.0
                    
                weekly_games.append({
                    "date": day_str,
                    "opponent": opponent,
                    "location": location,
                    "isHome": is_home,
                    "rainProb": rain_prob
                })
                found = True
                break
        if not found:
            weekly_games.append({
                "date": day_str,
                "opponent": "휴식",
                "location": "-",
                "isHome": False,
                "rainProb": 0.0
            })
            
    return weekly_games

def fetch_recent_game(target_team="삼성"):
    for i in range(0, 5):
        target_date = datetime.now() - timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")
        data = get_json(f'/schedule/games?upperCategoryId=kbaseball&date={date_str}')
        games = data.get('games', [])
        
        for g in games:
            if g.get('categoryId') == 'kbo' and (g.get('homeTeamName') == target_team or g.get('awayTeamName') == target_team):
                
                status = g.get('statusCode')
                if status not in ["RESULT", "STARTED", "BEFORE"]:
                    continue
                    
                gameId = g.get('gameId')
                
                # 기본값 세팅
                inning = "경기 전" if status == "BEFORE" else ("경기 종료" if status == "RESULT" else "경기 중")
                currentBatter = "-"
                currentPitcher = "-"
                batterAverage = "-"
                pitchCount = 0
                outs = 0; strikes = 0; balls = 0
                base1 = False; base2 = False; base3 = False
                
                if status == "STARTED":
                    # 실시간 릴레이 API 호출
                    relay_data = get_json(f'/schedule/games/{gameId}/relay')
                    text_relay = relay_data.get('textRelayData') or {}
                    cgs = text_relay.get('currentGameState', {})
                    
                    if cgs:
                        inning_num = text_relay.get('inn', 1)
                        homeOrAway = text_relay.get('homeOrAway', '초')
                        inning = f"{inning_num}회 {homeOrAway}"
                        
                        currentBatter = cgs.get('batter', '-')
                        currentPitcher = cgs.get('pitcher', '-')
                        
                        outs = int(cgs.get('out', 0))
                        strikes = int(cgs.get('strike', 0))
                        balls = int(cgs.get('ball', 0))
                        
                        base1 = cgs.get('base1', '0') == '1'
                        base2 = cgs.get('base2', '0') == '1'
                        base3 = cgs.get('base3', '0') == '1'

                return {
                    "gameId": gameId,
                    "homeTeam": g.get('homeTeamName'),
                    "awayTeam": g.get('awayTeamName'),
                    "homeScore": g.get('homeTeamScore', 0) or 0,
                    "awayScore": g.get('awayTeamScore', 0) or 0,
                    "status": status,
                    "inning": inning,
                    "currentBatter": currentBatter,
                    "currentPitcher": currentPitcher,
                    "batterAverage": batterAverage,
                    "pitchCount": pitchCount,
                    "outs": outs,
                    "strikes": strikes,
                    "balls": balls,
                    "base1": base1,
                    "base2": base2,
                    "base3": base3,
                    "winPitcher": g.get('winPitcherName', '-'),
                    "losePitcher": g.get('losePitcherName', '-'),
                    "savePitcher": g.get('savePitcherName', '-')
                }
    return None
