import scraper
from datetime import datetime, timedelta, timezone

target_team = "삼성"
fallback_game = None

for i in range(0, 5):
    target_date = datetime.now(timezone(timedelta(hours=9))) - timedelta(days=i)
    date_str = target_date.strftime("%Y-%m-%d")
    data = scraper.get_json(f'/schedule/games?upperCategoryId=kbaseball&date={date_str}')
    games = data.get('games', [])
    print(f"Checking {date_str}, found {len(games)} games")
    
    for g in games:
        if g.get('categoryId') == 'kbo' and (g.get('homeTeamName') == target_team or g.get('awayTeamName') == target_team):
            status = g.get('statusCode')
            print(f"  Game found: {g.get('homeTeamName')} vs {g.get('awayTeamName')}, status: {status}")
            
            if status in ["RESULT", "STARTED"]:
                print("  => Found RESULT/STARTED, returning")
                exit()
            elif status == "BEFORE" and fallback_game is None:
                print("  => Found BEFORE, saving as fallback")
                fallback_game = True

print("Returning fallback")
