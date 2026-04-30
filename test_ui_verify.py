from playwright.sync_api import sync_playwright
import time

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(1000)

    # Click on "Special Situation Arb" tab
    page.evaluate("switchMainTab('special_arb')")
    page.wait_for_timeout(500)

    # Note: I'll use the ID of the inputs since placeholder lookup might fail if it's different.
    # From grep: <input type="text" id="symbol-input" class="history-input" placeholder="e.g. RELIANCE" autocomplete="off">
    # Wait, the screenshot shows Buyback tab input. In specialSitTool.js we have 'bb-symbol' and 'ofs-symbol'.
    # Actually the general symbol input is: 'symbol-input' perhaps.
    # Let's inspect the workbench.html.

    page.locator("#bb-symbol").fill("WIPRO")
    page.wait_for_timeout(500)

    # Sync Prices
    # In workbench.html under Buyback: <button onclick="syncBuybackPrices(event)">Sync Prices</button>
    page.locator('button[onclick="syncBuybackPrices(event)"]').click()
    page.wait_for_timeout(3000)

    # Sync Holdings
    page.locator('button[onclick="syncBuybackHoldings(event)"]').click()
    page.wait_for_timeout(3000)

    page.screenshot(path="/home/jules/verification/screenshots/verification.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/videos", viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
