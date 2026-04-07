from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8000/workbench")
        page.wait_for_load_state("networkidle")

        # Use page.evaluate to force display the market-activity content
        page.evaluate("""
            document.querySelectorAll('.main-tab-content').forEach(e => e.style.display = 'none');
            const ma = document.getElementById('market-activity');
            if (ma) ma.style.display = 'block';

            // Try triggering render via module manager if it exists
            if (window.WorkbookManager && window.WorkbookManager.modules['market-activity']) {
                window.WorkbookManager.modules['market-activity'].render(ma);
            }
        """)

        time.sleep(2)

        # Call loadMarketActivity directly
        page.evaluate("if(typeof loadMarketActivity === 'function') { loadMarketActivity(); }")

        time.sleep(5)

        page.screenshot(path="verification_netoi12.png", full_page=True)
        print("Screenshot saved to verification_netoi12.png")
        browser.close()

run()
