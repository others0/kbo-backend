import requests
import datetime
import json

BASE = "https://api-gw.sports.naver.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

year = datetime.datetime.now().year
url = f"{BASE}/statistics/categories/kbo/seasons/{year}/teams"
res = requests.get(url, headers={"User-Agent": UA})
if res.status_code == 200:
    data = res.json().get('result', {}).get('seasonTeamStats', [])
    if data:
        print(json.dumps(data[0], indent=2, ensure_ascii=False))
    else:
        print("No data for", year)
        # Try 2024
        res2 = requests.get(f"{BASE}/statistics/categories/kbo/seasons/2024/teams", headers={"User-Agent": UA})
        print(json.dumps(res2.json().get('result', {}).get('seasonTeamStats', [])[0], indent=2, ensure_ascii=False))
