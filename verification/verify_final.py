from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    # 1. Check Adv Technicals (Volatility Analysis fix)
    print("Testing Adv Technicals...")
    page.evaluate("switchMainTab('derivatives')")
    page.wait_for_timeout(1000)
    page.evaluate("switchDerivTab('advtech')")
    page.wait_for_timeout(2000)
    # The canvas should now load instead of blank screen
    page.screenshot(path="/home/jules/verification/screenshots/adv_technicals_fixed.png", full_page=True)

    # 2. Check Market Activity (Nifty Overlay fix)
    print("Testing Market Activity...")
    page.evaluate("switchDerivTab('market')")
    page.wait_for_timeout(2000)
    page.screenshot(path="/home/jules/verification/screenshots/market_activity_nifty_line_fixed.png", full_page=True)

    # 3. Check Volatility Analysis
    print("Testing Volatility Analysis...")
    page.evaluate("switchDerivTab('optanalysis')")
    page.wait_for_timeout(2000)
    page.screenshot(path="/home/jules/verification/screenshots/vol_analysis_fixed.png", full_page=True)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
