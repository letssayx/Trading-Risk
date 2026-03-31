from playwright.sync_api import sync_playwright

def run_cuj(page):
    # Go to workbench
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    # Use button clicks instead of relying on global evaluated functions
    page.locator("text='Derivatives Analysis'").click()
    page.wait_for_timeout(1000)

    # 1. Volatility Analysis
    page.locator("#deriv-tab-btn-optanalysis").click()
    page.wait_for_timeout(1000)
    page.locator("#vol-analysis-symbol").fill("NIFTY")
    page.get_by_role("button", name="Load Volatility").click()
    page.wait_for_timeout(3000)

    page.screenshot(path="/app/verification/screenshots/volatility_analysis.png")
    page.wait_for_timeout(500)

    # 2. Market Activity
    page.locator("#deriv-tab-btn-market").click()
    page.wait_for_timeout(1000)
    page.get_by_role("button", name="Load Charts").click()
    page.wait_for_timeout(3000)

    page.screenshot(path="/app/verification/screenshots/market_activity.png")
    page.wait_for_timeout(500)

    # 3. Adv Technicals
    page.locator("#deriv-tab-btn-advtech").click()
    page.wait_for_timeout(1000)
    page.get_by_role("button", name="Load Chart").click()
    page.wait_for_timeout(3000)

    page.screenshot(path="/app/verification/screenshots/adv_technicals.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    import os
    os.makedirs("/app/verification/videos", exist_ok=True)
    os.makedirs("/app/verification/screenshots", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/app/verification/videos",
            viewport={'width': 1600, 'height': 900}
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
