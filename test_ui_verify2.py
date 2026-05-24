from playwright.sync_api import sync_playwright
import os
import glob

def run_cuj(page):
    # Mock the API responses since DB is not working
    page.route("**/api/data/view/list?type=dividend*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body="""[
            {"symbol":"OFSS","broadcast_date":"2026-05-24T12:10:46","purpose":"Dividend","dividend_type":"Interim","parsed_dividend_amount":50.0,"is_synthetic":false}
        ]"""
    ))
    page.route("**/api/data/view/list?type=board_meeting*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body="""[
            {"symbol":"OFSS","broadcast_date":"2026-05-24T12:10:46","meeting_date":"2026-05-25","purpose":"Board Meeting","is_synthetic":false}
        ]"""
    ))

    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(1000)

    try:
        page.click(".main-tab[data-target='dividends']")
        page.wait_for_timeout(1000)

        page.fill("#div-symbol-search", "OFSS")
        page.wait_for_timeout(500)
        page.click("button[onclick='loadDividendsData()']")

        page.wait_for_timeout(3000)

        os.makedirs("/home/jules/verification/screenshots", exist_ok=True)
        page.screenshot(path="/home/jules/verification/screenshots/verification2.png")
        page.wait_for_timeout(1000)
    except Exception as e:
        print(f"Error in CUJ: {e}")
        page.screenshot(path="/home/jules/verification/screenshots/error2.png")

if __name__ == "__main__":
    os.makedirs("/home/jules/verification/videos", exist_ok=True)
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
