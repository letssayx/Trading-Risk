from playwright.sync_api import sync_playwright

def test_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8000/workbench")

        # Click Historical Data tab
        page.evaluate("switchMainTab('historical')")
        page.wait_for_timeout(1000)
        page.locator("#dataType").click()
        page.wait_for_timeout(500)
        page.screenshot(path="/home/jules/verification/historical_fii_dii.png", full_page=True)

        # Click Import Data tab
        page.locator(".main-tab[data-target='import']").click()
        page.wait_for_timeout(1000)
        page.screenshot(path="/home/jules/verification/import_fii_dii.png", full_page=True)

        browser.close()

if __name__ == "__main__":
    test_ui()
