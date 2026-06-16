import requests

url = "https://www.koreabaseball.com/Game/Sms.aspx?gameId=20240616WOSS0&section=PLAYBYPLAY" # Past game for testing
res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
print(res.status_code)
print(res.text[:1000])

