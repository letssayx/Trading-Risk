from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    # Click on "Rollover Analysis" tab
    try:
        page.evaluate("switchMainTab('derivatives')")
        page.wait_for_timeout(1000)
        page.evaluate("switchDerivTab('rollover')")
        page.wait_for_timeout(1000)
    except:
        pass

    page.wait_for_timeout(2000)

    # Take screenshot of Rollover tab
    page.screenshot(path="/tmp/rollover_ui_check.png")
    page.wait_for_timeout(1000)

    # Test expanding a history row
    try:
        # Click the first row expansion if it exists
        page.locator(".roll-row").first.click()
        page.wait_for_timeout(1000)
    except:
        pass

    page.screenshot(path="/tmp/rollover_history_check.png")
    page.wait_for_timeout(500)

    # Also check OI Analysis tab
    try:
        page.evaluate("switchDerivTab('oi')")
        page.wait_for_timeout(2000)

        # Click first row expansion
        page.locator(".deriv-row").first.click()
        page.wait_for_timeout(1000)

        page.screenshot(path="/tmp/oi_history_check.png")
    except:
        pass

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/tmp/videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
