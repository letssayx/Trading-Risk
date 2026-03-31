import os
from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    # Switch to Derivatives Analysis tab
    page.evaluate("switchMainTab('derivatives')")
    page.wait_for_timeout(1000)

    # Market Activity
    page.evaluate("switchDerivTab('market')")
    page.wait_for_timeout(1000)
    page.evaluate("document.querySelector('#deriv-tab-market button').click()")
    page.wait_for_timeout(4000)
    page.screenshot(path="/home/jules/verification/screenshots/market_activity_nifty_line.png", full_page=True)

    # Adv Technicals
    page.evaluate("switchDerivTab('advtech')")
    page.wait_for_timeout(1000)
    page.evaluate("loadDynamicChart()")
    page.wait_for_timeout(4000)
    page.screenshot(path="/home/jules/verification/screenshots/adv_technicals.png", full_page=True)

    # Try downloading CSV from Adv Technicals
    page.evaluate("""
        const btns = document.querySelectorAll('#deriv-tab-advtech button');
        for (let btn of btns) {
            if (btn.innerText.includes('CSV')) {
                btn.click();
                break;
            }
        }
    """)
    page.wait_for_timeout(2000)

    # Volatility Analysis
    page.evaluate("switchDerivTab('optanalysis')")
    page.wait_for_timeout(1000)
    page.evaluate("document.querySelector('#deriv-tab-optanalysis button').click()")
    page.wait_for_timeout(4000)
    page.screenshot(path="/home/jules/verification/screenshots/volatility_analysis.png", full_page=True)

    # Try downloading CSV from Volatility Analysis
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