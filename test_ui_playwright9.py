from playwright.sync_api import sync_playwright, expect
import time

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/video")
        page = context.new_page()

        print("Navigating to UI...")
        page.goto("http://localhost:8000/workbench")
        page.wait_for_timeout(2000)

        # Test Autocomplete
        print("Testing Autocomplete keyboard nav on 'div-symbol-search'...")
        search_input = page.locator("#div-symbol-search")
        search_input.wait_for(state="visible", timeout=5000)

        search_input.fill("HD")
        page.wait_for_timeout(1000) # give JS time to build dropdown

        print("Pressing ArrowDown...")
        search_input.press("ArrowDown")
        page.wait_for_timeout(1000)

        print("Pressing Enter...")
        search_input.press("Enter")
        page.wait_for_timeout(2000)

        print("Taking screenshot...")
        page.screenshot(path="/home/jules/verification/verification.png")
        page.wait_for_timeout(1000)

        context.close()
        browser.close()
        print("Done.")

if __name__ == "__main__":
    verify_ui()
