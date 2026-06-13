import subprocess
import time
from playwright.sync_api import sync_playwright

def verify_ui():
    print("Starting app...")
    server = subprocess.Popen(["python3", "-m", "uvicorn", "backend.main:app", "--port", "8000"])
    time.sleep(5) # wait for server to start

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(record_video_dir="/home/jules/verification/")
            page = context.new_page()

            print("Navigating to workbench...")
            page.goto("http://localhost:8000/workbench")

            # Wait for specific selectors that should be present
            page.wait_for_selector("text=Market Analysis")

            # Click the tab using JS as requested in AGENTS.md
            page.evaluate("switchMainTab('market_activity')")
            time.sleep(2)

            page.screenshot(path="/home/jules/verification/fii_analysis.png")

            context.close()
            browser.close()
            print("Done")
    finally:
        server.terminate()
        server.wait()

if __name__ == "__main__":
    import os
    os.makedirs("/home/jules/verification", exist_ok=True)
    verify_ui()
