from playwright.sync_api import sync_playwright
import os
import glob

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(1000)

    # Click Dividends Data Bank tab
    try:
        # Assuming the tab has data-target="dividends"
        page.click("text=Dividends Data Bank")
        page.wait_for_timeout(1000)

        # Load OFSS data directly by modifying input
        page.fill("#div-symbol-search", "OFSS")
        page.wait_for_timeout(500)
        page.click("button[onclick='loadDividendsData()']")

        # Wait for data to load
        page.wait_for_timeout(3000)

        # Screenshot the result
        os.makedirs("/home/jules/verification/screenshots", exist_ok=True)
        page.screenshot(path="/home/jules/verification/screenshots/verification.png")
        page.wait_for_timeout(1000)
    except Exception as e:
        print(f"Error in CUJ: {e}")
        page.screenshot(path="/home/jules/verification/screenshots/error.png")

if __name__ == "__main__":
    # Clear old videos
    os.makedirs("/home/jules/verification/videos", exist_ok=True)
    for f in glob.glob("/home/jules/verification/videos/*.webm"):
        os.remove(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
