from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.koreabaseball.com/Game/LiveText.aspx?leagueId=1&seriesId=0&gameId=20260616WOSS0&gyear=2026")
    page.wait_for_timeout(3000)
    
    html = page.content()
    with open("livetext_dump.html", "w") as f:
        f.write(html)
    
    print("Saved rendered LiveText HTML to livetext_dump.html")
    browser.close()
