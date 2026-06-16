import scraper
for d in ["2026-06-16", "2026-06-19", "2026-06-20"]:
    data = scraper.get_json(f'/schedule/games?upperCategoryId=kbaseball&date={d}')
    games = data.get('games', [])
    for g in games:
        if g.get('categoryId') == 'kbo' and (g.get('homeTeamName') == '삼성' or g.get('awayTeamName') == '삼성'):
            print(f"Requested {d} -> API Returned {g.get('gameDate')}: {g.get('homeTeamName')} vs {g.get('awayTeamName')}")
