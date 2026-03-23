from playwright.sync_api import Page, expect, sync_playwright
import time
import json

def verify_feature(page: Page):
    # Mock the API responses before navigating
    def handle_mwpl(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"data": {
                "RELIANCE": [
                    {"date": "2024-03-20", "eq_close": 2900.5, "fut1_close": 2910.0, "mwpl": 45.5, "mwpl_array": [{"Client 1": 25.0}, {"Client 2": 20.5}]},
                    {"date": "2024-03-19", "eq_close": 2880.0, "fut1_close": 2895.0, "mwpl": 42.0, "mwpl_array": [{"Client 1": 22.0}, {"Client 2": 20.0}]}
                ],
                "TCS": [
                    {"date": "2024-03-20", "eq_close": 3950.0, "fut1_close": 3965.0, "mwpl": 35.2, "mwpl_array": [{"Client 1": 35.2}]}
                ]
            }})
        )

    page.route("**/api/data/derivatives/mwpl_historical", handle_mwpl)

    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(1500)

    # Open Derivatives Analysis tab
    page.evaluate("switchMainTab('derivatives')")
    page.wait_for_timeout(500)

    # Click MWPL Analysis tab
    page.evaluate("switchDerivTab('mwpl')")
    page.wait_for_timeout(500)

    page.click("text='Refresh MWPL Data'")
    page.wait_for_timeout(1500)

    # Expand the history for reliance
    page.click("text='RELIANCE'")
    page.wait_for_timeout(1000)

    page.screenshot(path="/home/jules/verification/mwpl.png")

    # Check that MWPL tab doesn't bleed to market watch
    page.evaluate("switchMainTab('marketwatch')")
    page.wait_for_timeout(1000)
    page.screenshot(path="/home/jules/verification/marketwatch.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        import os
        os.makedirs("/home/jules/verification/video", exist_ok=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/video")
        page = context.new_page()
        try:
            verify_feature(page)
        finally:
            context.close()
            browser.close()
