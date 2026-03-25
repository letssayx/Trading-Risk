import os
import time
from playwright.sync_api import sync_playwright

def verify_feature(page):
    print("Navigating to workbench...")
    page.goto("http://127.0.0.1:8000/workbench")
    page.wait_for_timeout(2000)

    # Wait for Market Watch Data to load by default, or we can click MWPL Analysis
    print("Clicking Derivatives tab...")
    page.click("text=Derivatives")
    page.wait_for_timeout(1000)

    print("Clicking MWPL Analysis tab...")
    page.click("text=MWPL Analysis")
    page.wait_for_timeout(1000)

    print("Clicking Refresh MWPL Data...")
    page.click("text=Refresh MWPL Data")
    page.wait_for_timeout(4000) # Wait for API to load

    print("Taking screenshot...")
    page.screenshot(path="/home/jules/verification/verification.png")
    page.wait_for_timeout(1000)
    print("Verification script finished.")

if __name__ == "__main__":
    # Create verification dirs
    os.makedirs("/home/jules/verification/video", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/video")
        page = context.new_page()
        try:
            verify_feature(page)
        except Exception as e:
            print("Error:", e)
        finally:
            context.close()
            browser.close()
