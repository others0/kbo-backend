from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

# 앱에서 서버로 접근할 수 있도록 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 이 변수들에 실제 네이버/KBO 크롤링 결과값을 업데이트합니다.
live_data = {
    "inning": "1회 초",
    "homeScore": 0,
    "awayScore": 0,
    "homeTeam": "삼성",
    "awayTeam": "LG",
    "outs": 0,
    "strikes": 0,
    "balls": 0,
    "currentBatter": "구자욱",
    "batterAverage": "0.336",
    "currentPitcher": "원태인",
    "pitchCount": 0,
    "base1": False,
    "base2": False,
    "base3": False
}

batters_home = ["구자욱", "김지찬", "류지혁", "강민호", "이재현"]
batters_away = ["홍창기", "박해민", "오지환", "오스틴", "문보경"]
pitchers_home = ["원태인", "뷰캐넌", "오승환"]
pitchers_away = ["켈리", "플럿코", "고우석"]

import scraper

# 선수들의 실제 타율 (2024년 시즌 기준 대략적인 값)
batter_stats = {
    "구자욱": "0.336",
    "김지찬": "0.292",
    "류지혁": "0.268",
    "강민호": "0.290",
    "이재현": "0.249",
    "홍창기": "0.332",
    "박해민": "0.285",
    "오지환": "0.268",
    "오스틴": "0.313",
    "문보경": "0.282"
}

def update_mock_data():
    """백그라운드에서 크롤러를 통해 네이버 스포츠 데이터를 가져옵니다."""
    
    # 1. 최신 순위 가져오기
    standings = scraper.fetch_standings()
    if standings:
        live_data["standings"] = standings
        
    # 2. 이번주 삼성 일정 가져오기
    schedule = scraper.fetch_weekly_schedule("삼성")
    if schedule:
        live_data["schedule"] = schedule
        
    # 3. 최근에 끝난 경기(또는 진행 중인 경기) 정보 가져오기
    game = scraper.fetch_recent_game("삼성")
    if game:
        live_data["homeScore"] = game["homeScore"]
        live_data["awayScore"] = game["awayScore"]
        live_data["inning"] = game["inning"]
        live_data["currentBatter"] = game["currentBatter"]
        live_data["currentPitcher"] = game["currentPitcher"]
        
        # 샌드박스용 가짜 스트라이크 카운트 로직을 전부 삭제하고,
        # scraper가 가져온 "진짜 데이터"를 100% 라이브 데이터에 매핑합니다.
        live_data["outs"] = game.get("outs", 0)
        live_data["strikes"] = game.get("strikes", 0)
        live_data["balls"] = game.get("balls", 0)
        live_data["base1"] = game.get("base1", False)
        live_data["base2"] = game.get("base2", False)
        live_data["base3"] = game.get("base3", False)
        live_data["pitchCount"] = game.get("pitchCount", 0)
        
        # 경기 상태 및 투수 기록 (승/패/세이브) 매핑
        live_data["status"] = game.get("status", "BEFORE")
        live_data["winPitcher"] = game.get("winPitcher", "-")
        live_data["losePitcher"] = game.get("losePitcher", "-")
        live_data["savePitcher"] = game.get("savePitcher", "-")
                
        # 타율 매핑
        if live_data["currentBatter"] in batter_stats:
            live_data["batterAverage"] = batter_stats[live_data["currentBatter"]]
        else:
            live_data["batterAverage"] = "0.280"

@app.get("/live")
def get_live_data():
    update_mock_data()
    return live_data

@app.get("/")
def read_root():
    return {"message": "KBO Scoreboard Server is running"}
