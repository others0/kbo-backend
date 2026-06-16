import requests

BASE = "https://api-gw.sports.naver.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

def get_json(path):
    url = f"{BASE}{path}"
    headers = {"User-Agent": UA}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json().get('result', {})
    return {}

print("Standings:", get_json('/statistics/categories/kbo/seasons/2024/teams').keys())
print("Schedule:", get_json('/schedule/games?upperCategoryId=kbaseball&date=2024-06-17').keys())
