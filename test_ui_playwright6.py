from playwright.sync_api import sync_playwright, expect
import time

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/video")
        page = context.new_page()

        print("Navigating to UI...")
        page.goto("http://localhost:8000/")
        page.wait_for_timeout(2000)

        # Taking a screenshot to see what's actually rendering
        page.screenshot(path="/home/jules/verification/debug.png")

        html_content = page.content()
        if "Dividends" in html_content:
            print("Dividends text found in HTML!")
        else:
            print("Dividends text NOT found. Are we at the right URL?")

        print("Done.")

if __name__ == "__main__":
    verify_ui()
