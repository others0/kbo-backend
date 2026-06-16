from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://m.sports.naver.com/kbaseball/schedule/index")
    page.wait_for_timeout(3000)
    page.screenshot(path="naver_schedule.png")
    
    # Try clicking the first game to go to text relay
    game_links = page.query_selector_all("a.MatchBox_link__2gG-F") # Guessing selector, maybe just find "중계"
    
    browser.close()
