from playwright.sync_api import sync_playwright
import os
def run_cuj(page):
    page.route('**/api/special-sit/dividends', lambda route: route.fulfill(status=200, content_type='application/json', body='[{"symbol":"RELIANCE","lot_size":250,"spot":2950.0,"sector":"Oil & Gas","futures":[],"last_type":"Final","last_ex_date":"10-08-2025","last_amount":10.0,"is_above_2_percent":false,"board_meeting_date":null,"broadcast_date":null,"expected_amount":10.0,"expected_amount_compare":10.0,"expected_type":"Final","expected_highly_likely":"Forecasted: 10-08-2026","expected_less_likely":"Amount declared, date not yet announced","history":[{"amount":10.0,"ex_date":"Record date not yet declared","dividend_type":"Final","is_above_2_percent":false}]}]'))
    page.goto('http://localhost:8000/workbench')
    page.wait_for_timeout(1000)
    try:
        page.click("text=Special Situation Arb")
        page.wait_for_timeout(3000)
        os.makedirs('/home/jules/verification/screenshots', exist_ok=True)
        page.screenshot(path='/home/jules/verification/screenshots/reliance_special_sit.png')
    except Exception as e:
        print(e)
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
