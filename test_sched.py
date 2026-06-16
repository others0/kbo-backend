import scraper
games = scraper.fetch_weekly_schedule("삼성")
for g in games:
    print(g)
