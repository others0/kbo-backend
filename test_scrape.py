import requests
from bs4 import BeautifulSoup

url = "https://sports.naver.com/kbaseball/schedule/index.nhn?date=20240618&month=06&year=2024"
res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
print(res.status_code)
print(len(res.text))
