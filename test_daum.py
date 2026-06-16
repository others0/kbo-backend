import requests
import json

url = "https://sports.daum.net/prx/p/sports/game/list/schedule.json?leagueCode=kbo&seasonKey=2024&month=202406"
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(url, headers=headers)
print(res.status_code)
print(res.text[:500])
