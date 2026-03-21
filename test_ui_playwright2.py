from playwright.sync_api import sync_playwright, expect
import time

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/video")
        page = context.new_page()

        print("Navigating to UI...")
        page.goto("http://localhost:8000/ui")
        page.wait_for_timeout(2000)

        print("Opening Dividends Tab using selector...")
        # Looks like the tab might be an icon or different text
        tabs = page.locator(".sidebar-item")

        # Click the tab that opens dividends (we'll try to guess based on standard workbench structure)
        # We can also just run the JS command to switch to it
        page.evaluate("if(typeof switchMainTab === 'function') switchMainTab('dividends')")
        page.wait_for_timeout(1000)

        # Test Autocomplete
        print("Testing Autocomplete keyboard nav on 'div-symbol-search'...")
        search_input = page.locator("#div-symbol-search")
        search_input.fill("HD")
        page.wait_for_timeout(500)

        # Test keyboard nav
        search_input.press("ArrowDown")
        page.wait_for_timeout(500)
        search_input.press("Enter")
        page.wait_for_timeout(1000)

        print("Taking screenshot...")
        page.screenshot(path="/home/jules/verification/verification.png")
        page.wait_for_timeout(1000)

        context.close()
        browser.close()
        print("Done.")

if __name__ == "__main__":
    verify_ui()
