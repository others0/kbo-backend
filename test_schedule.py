import requests
import json
import datetime

url = "https://api-gw.sports.naver.com/schedule/games?upperCategoryId=kbaseball&date=2026-06-17"
res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
if res.status_code == 200:
    data = res.json()
    games = data.get('result', {}).get('games', [])
    for g in games:
        if g.get('categoryId') == 'kbo':
            print(json.dumps(g, indent=2, ensure_ascii=False))
            break
