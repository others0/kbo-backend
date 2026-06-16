import requests
from bs4 import BeautifulSoup

url = "https://www.koreabaseball.com/Schedule/Schedule.aspx"
res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(res.text, 'html.parser')
# Find the schedule table
table = soup.find('table', class_='tData')
if table:
    print("Found table!")
    for row in table.find('tbody').find_all('tr')[:10]:
        print([td.text.strip() for td in row.find_all('td')])
