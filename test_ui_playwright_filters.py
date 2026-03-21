from playwright.sync_api import Page, expect, sync_playwright
import time
import os
import glob

def verify_feature(page: Page):
    print("Navigating to local UI...")
    page.goto("http://localhost:8000")
    page.wait_for_timeout(2000)

    print("Opening Dividends Data Bank Tab...")
    # Click Dividends Tab
    page.evaluate("switchMainTab('dividends')")
    page.wait_for_timeout(1000)

    # Search for TCS
    print("Typing in search box...")
    search_input = page.locator("#div-symbol-search")
    search_input.fill("TCS")
    page.wait_for_timeout(1000)

    # Change dropdown to Final
    print("Selecting Type filter...")
    type_dropdown = page.locator("#div-type-filter")
    type_dropdown.select_option("Final")
    page.wait_for_timeout(1000)

    # Check F&O only
    print("Checking F&O Stocks Only box...")
    fo_checkbox = page.locator("#div-fo-only-filter")
    fo_checkbox.check()
    page.wait_for_timeout(1000)

    # Click Load Data
    print("Clicking Load Data...")
    load_btn = page.locator("button:has-text('Load Data')")
    load_btn.click()
    page.wait_for_timeout(3000) # Give it time to fetch API and render

    # Take screenshot of the result
    print("Taking screenshot...")
    page.screenshot(path="/home/jules/verification/verification2.png")
    page.wait_for_timeout(1000)

    # We won't test downloading CSV since we can't easily verify the blob in a simple script
    # But the UI state should show our filters and the updated table headers.

if __name__ == "__main__":
    # Clean up old videos
    for f in glob.glob("/home/jules/verification/video/*.webm"):
        os.remove(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/video",
            viewport={"width": 1400, "height": 900}
        )
        page = context.new_page()
        try:
            verify_feature(page)
        except Exception as e:
            print(f"Error during verification: {e}")
        finally:
            context.close()
            browser.close()
            print("Finished.")
