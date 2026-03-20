from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # use file scheme to view static workbench
        page.goto("file:///app/backend/ui/templates/workbench.html")
        page.wait_for_timeout(1000)
        page.evaluate("switchMainTab('tab-dividends', null)")
        page.wait_for_timeout(1000)
        page.evaluate("switchDividendsTab('meetings')")
        page.wait_for_timeout(1000)
        page.screenshot(path="/home/jules/verification/verification.png")
        browser.close()

if __name__ == "__main__":
    main()
