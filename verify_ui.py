from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8000/workbench")
        page.wait_for_load_state("networkidle")

        # Click the tab
        try:
            page.locator('.main-tab[data-target="market-activity"]').click(timeout=3000)
        except Exception:
            pass

        try:
            page.locator('li[data-target="market-activity"]').click(timeout=3000)
        except Exception:
            pass

        # Load participant OI
        page.locator('#btn-load-participant-oi').click()
        time.sleep(4)

        page.screenshot(path="verification_netoi5.png", full_page=True)
        print("Screenshot saved to verification_netoi5.png")
        browser.close()

run()
