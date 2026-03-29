from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Log console messages
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser error: {err}"))

        page.goto("http://127.0.0.1:8000/workbench")

        print("Navigating to Derivatives Analysis...")
        page.get_by_text("Derivatives Analysis", exact=True).click()
        page.wait_for_timeout(1000)

        print("Navigating to Market Activity...")
        page.get_by_text("Market Activity", exact=True).click()
        # Ensure that the days dropdown is set and load charts is clicked if needed
        # Or just wait since it should auto-load or we can click Load Charts
        try:
            page.get_by_text("Load Charts").click()
        except Exception as e:
            pass

        page.wait_for_timeout(5000)
        page.screenshot(path="market_activity_charts.png", full_page=True)
        print("Market Activity screenshot saved.")

        browser.close()

run()
