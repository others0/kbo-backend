import requests
from bs4 import BeautifulSoup

url = "https://www.koreabaseball.com/Game/LiveText.aspx?leagueId=1&seriesId=0&gameId=20260616WOSS0&gyear=2026"
res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
print("Status Code:", res.status_code)

soup = BeautifulSoup(res.text, "html.parser")
print("Title:", soup.title.string if soup.title else None)

# 문자중계 내용이 어디에 있는지 찾아보기
live_list = soup.find(id="tblPlayByPlayList")
if live_list:
    print("Found tblPlayByPlayList!")
    print(live_list.text[:500])
else:
    print("tblPlayByPlayList NOT found. Let's dump a little html.")
    print(res.text[:1000])
