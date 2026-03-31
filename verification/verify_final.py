import os
from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    # 1. Switch to Derivatives Analysis tab
    page.evaluate("switchMainTab('derivatives')")
    page.wait_for_timeout(1000)

    # 2. Switch to Market Activity Tab
    page.evaluate("switchDerivTab('market')")
    page.wait_for_timeout(2000)

    # Click Load Charts to get Market Activity NIFTY charts
    print("Loading Market Activity charts...")
    page.evaluate("document.querySelector('#deriv-tab-market button').click()")
    page.wait_for_timeout(5000)

    # Take screenshot of market activity
    page.screenshot(path="/home/jules/verification/screenshots/market_activity_final.png", full_page=True)
    page.wait_for_timeout(1000)

    # 3. Switch to Volatility Analysis Tab
    page.evaluate("switchDerivTab('optanalysis')")
    page.wait_for_timeout(1000)

    # Set NIFTY symbol
    page.evaluate("document.getElementById('vol-analysis-symbol').value = 'NIFTY'")

    # Click Load Volatility
    print("Loading Volatility charts...")
    page.evaluate("document.querySelector('#deriv-tab-optanalysis button').click()")
    page.wait_for_timeout(5000)

    # Download CSV
    print("Testing CSV download...")
    page.evaluate("""
        const btns = document.querySelectorAll('#deriv-tab-optanalysis button');
        for (let btn of btns) {
            if (btn.innerText.includes('CSV')) {
                btn.click();
                break;
            }
        }
    """)
    page.wait_for_timeout(2000)

    # Take screenshot of volatility
    page.screenshot(path="/home/jules/verification/screenshots/volatility_final.png", full_page=True)
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    os.makedirs("/home/jules/verification/videos", exist_ok=True)
    os.makedirs("/home/jules/verification/screenshots", exist_ok=True)

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