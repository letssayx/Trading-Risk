from playwright.sync_api import sync_playwright

def test_britannia_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('http://localhost:8000/workbench')

        # Load Special Arb Tab
        page.evaluate("switchMainTab('special_arb')")
        page.wait_for_timeout(2000) # wait for data load

        # Click the 'Dividends' Sub-Tab inside Special Arb
        page.evaluate("switchSpecialSitTab('dividends')")
        page.wait_for_timeout(2000)

        # We don't have db populated since we just spun it up freshly using docker and didn't run import tasks
        # Let's take screenshot anyway to see it's alive
        page.screenshot(path='britannia_fix_screenshot.png')
        browser.close()

if __name__ == "__main__":
    test_britannia_ui()
