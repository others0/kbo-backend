from playwright.sync_api import sync_playwright
import time
import re

def parse_kbo_schedule(year="2024", month="06"):
    games = []
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
            
            # 첫 번째 열이 날짜인 경우 (rowspan 적용됨)
            if len(texts) == 9:
                current_date = texts[0]
                time_str = texts[1]
                match_str = texts[2]
                location = texts[7]
                note = texts[8]
            else:
                time_str = texts[0]
                match_str = texts[1]
                location = texts[6]
                note = texts[7]
                
            # match_str 파싱: "NC6vs2한화" -> away: NC, awayScore: 6, homeScore: 2, homeTeam: 한화
            # "SSGvs롯데" -> away: SSG, awayScore: 0, homeScore: 0, homeTeam: 롯데
            m = re.match(r"([A-Za-z가-힣]+)(\d*)vs(\d*)([A-Za-z가-힣]+)", match_str)
            if m:
                awayTeam = m.group(1)
                awayScore = int(m.group(2)) if m.group(2) else 0
                homeScore = int(m.group(3)) if m.group(3) else 0
                homeTeam = m.group(4)
                
                status = "RESULT" if m.group(2) else "BEFORE"
                if note == "우천취소":
                    status = "CANCEL"
                    
                games.append({
                    "date": current_date,
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
    return games

if __name__ == "__main__":
    games = parse_kbo_schedule()
    print(f"Parsed {len(games)} games")
    print(games[50])
