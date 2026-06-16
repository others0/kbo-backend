import requests

url = "https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList"
data = {"leId": "1", "srIdList": "0,1,3,4,5,7,9", "cbMonth": "06", "cbYear": "2024"}
headers = {'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'Mozilla/5.0'}
res = requests.post(url, data=data, headers=headers)
print(res.status_code)
print(res.text[:500])

url_rank = "https://www.koreabaseball.com/ws/TeamRank.asmx/GetTeamRankList"
# maybe it has an API?
