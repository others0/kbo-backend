import requests
from bs4 import BeautifulSoup
url = "https://www.koreabaseball.com/TeamRank/TeamRank.aspx"
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, 'html.parser')
table = soup.select_one('table.tData tbody')
if table:
    for row in table.select('tr')[:5]:
        cols = row.select('td')
        print([c.text.strip() for c in cols])
else:
    print("Table not found on KBO")
