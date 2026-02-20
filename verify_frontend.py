from playwright.sync_api import sync_playwright

def verify_turtle_table():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to workbench...")
        try:
            page.goto("http://127.0.0.1:8000/workbench")

            # Wait for page to settle
            page.wait_for_timeout(2000)

            # Click the tab if needed. The screenshot shows tabs.
            # Let's try to find the button.
            # Assuming it's a button or div with text "Turtle Legacy"
            # If not found, just take a screenshot anyway to see what loaded.
            try:
                page.get_by_text("Turtle Legacy").click()
                print("Clicked Turtle Legacy tab")
            except:
                print("Could not find/click Turtle Legacy tab, maybe it is already active or failed to load")

            page.wait_for_timeout(1000)

            # Check for headers
            headers = page.locator("th").all_inner_texts()
            print(f"Table Headers found: {headers}")

            if "OI" in headers and "Volume" in headers:
                print("SUCCESS: OI and Volume headers found.")
            else:
                print("FAILURE: Missing headers.")

            page.screenshot(path="verification_turtle_table.png")
            print("Screenshot saved to verification_turtle_table.png")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_turtle_table()
