from playwright.sync_api import Page, expect, sync_playwright
import time
import os
import glob

def verify_feature(page: Page):
    print("Navigating to local UI...")
    page.goto("http://localhost:8000")
    page.wait_for_timeout(2000)

    print("Forcing style...")
    page.evaluate("""
        document.querySelectorAll('.main-tab-content').forEach(el => { el.style.display = 'none'; el.classList.remove('active'); });
        document.getElementById('tab-dividends').style.display = 'block';
        document.getElementById('tab-dividends').classList.add('active');
    """)
    page.wait_for_timeout(1000)

    print("Typing in search box...")
    search_input = page.locator("#div-symbol-search")
    search_input.fill("TCS")
    page.wait_for_timeout(1000)

    print("Selecting Type filter...")
    type_dropdown = page.locator("#div-type-filter")
    type_dropdown.select_option("Final")
    page.wait_for_timeout(1000)

    print("Checking F&O Stocks Only box...")
    fo_checkbox = page.locator("#div-fo-only-filter")
    fo_checkbox.check()
    page.wait_for_timeout(1000)

    print("Clicking Load Data...")
    load_btn = page.locator("#tab-dividends button", has_text="Load Data")
    load_btn.click()
    page.wait_for_timeout(3000)

    print("Taking screenshot...")
    page.screenshot(path="/home/jules/verification/verification.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
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
