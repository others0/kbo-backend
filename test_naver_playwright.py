from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://m.sports.naver.com/kbaseball/schedule/index")
    page.wait_for_timeout(3000)
    print(page.title())
    print("HTML Preview:", page.content()[:500])
    browser.close()
