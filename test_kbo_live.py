from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.koreabaseball.com/Schedule/GameCenter/Main.aspx")
    page.wait_for_timeout(4000)
    
    # KBO 게임센터는 오늘 날짜 기준으로 경기가 없으면 빈 화면이 뜸.
    # 경기가 있다면 상단 스코어보드, 또는 문자중계 탭이 있을 것임.
    # 페이지 내용을 좀 덤프해보자
    html = page.content()
    
    with open("kbo_live_dump.html", "w") as f:
        f.write(html)
        
    print("Saved HTML to kbo_live_dump.html")
    browser.close()
