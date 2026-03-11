from playwright.sync_api import sync_playwright

def test_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8000/workbench")

        # Wait for the derivatives tab and click it
        page.locator(".main-tab[data-target='derivatives']").click()
        page.wait_for_timeout(2000)

        # Take screenshot of the headers
        page.screenshot(path="/home/jules/verification/derivatives_headers.png", full_page=True)

        browser.close()

if __name__ == "__main__":
    test_ui()
