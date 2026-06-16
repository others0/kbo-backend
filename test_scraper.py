import requests
from bs4 import BeautifulSoup

url = "https://statiz.sporki.com/team/"
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, 'html.parser')
table = soup.select_one('table')
if table:
    for row in table.select('tr')[:5]:
        cols = row.select('td, th')
        print([c.text.strip() for c in cols])
else:
    print("Table not found")
