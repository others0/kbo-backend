import scraper
from datetime import datetime, timedelta, timezone

today = datetime.now(timezone(timedelta(hours=9)))
start_of_week = today - timedelta(days=today.weekday())

for i in range(7):
    target_date = start_of_week + timedelta(days=i)
    date_str = target_date.strftime("%Y-%m-%d")
    data = scraper.get_json(f'/schedule/games?upperCategoryId=kbaseball&date={date_str}')
    games = data.get('games', [])
    print(f"--- {date_str} ---")
    for g in games:
        if g.get('categoryId') == 'kbo':
            print(f"  {g.get('homeTeamName')} vs {g.get('awayTeamName')} ({g.get('statusCode')}) - HomeScore: {g.get('homeTeamScore')}, AwayScore: {g.get('awayTeamScore')}")

print("\n--- Weekly Schedule ---")
print(scraper.fetch_weekly_schedule('삼성'))

