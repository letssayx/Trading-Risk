from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(record_video_dir="/home/jules/verification/video", viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # Navigate to the main page where workbench.html is served
        # We'll just load the file directly to bypass needing the exact FastAPI route mapping
        import os
        page.goto(f"file://{os.path.abspath('backend/ui/templates/workbench.html')}")
        page.wait_for_timeout(3000)

        # Take a screenshot of the UI view
        page.screenshot(path="/home/jules/verification/default_view.png")

        print("Clicking Dividends Data Bank...")
        tab = page.locator('div[data-target="dividends"]')
        if tab.is_visible():
            tab.click()
            page.wait_for_timeout(1000)
            page.screenshot(path="/home/jules/verification/dividends_tab.png")
            print("Captured Dividends Tab")

        # Test Autocomplete in Historical Data
        print("Clicking Historical Data...")
        history_tab = page.locator('div[data-target="history"]')
        if history_tab.is_visible():
            history_tab.click()
            page.wait_for_timeout(1000)

            symbol_input = page.locator("#symbol-input")
            symbol_input.fill("RELIANCE")
            page.wait_for_timeout(500)

            # Show dropdown
            page.screenshot(path="/home/jules/verification/autocomplete_dropdown.png")

            symbol_input.press("Enter")
            page.wait_for_timeout(2000)

            page.screenshot(path="/home/jules/verification/historical_autocomplete.png")
            print("Captured Historical Data autocomplete")

        context.close()
        browser.close()
        print("Done")

if __name__ == "__main__":
    run()
