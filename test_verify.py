from playwright.sync_api import Page, expect, sync_playwright

def verify_feature(page: Page):
    print("Navigating to the application...")
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(4000)

    # Click History Tab
    print("Clicking History Tab...")
    page.locator("div.main-tab[data-target='history']").click()
    page.wait_for_timeout(1000)

    # Select MWPL Data Type
    print("Selecting MWPL...")
    page.locator("#data-type").select_option("mwpl")
    page.wait_for_timeout(1000)

    # Check Latest
    print("Checking Latest...")
    # It should be checked by default, just click load
    page.get_by_role("button", name="Load Data").click()
    page.wait_for_timeout(3000)

    print("Taking screenshot...")
    page.screenshot(path="/home/jules/verification/verification.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/video")
        page = context.new_page()
        try:
            verify_feature(page)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            context.close()
            browser.close()
