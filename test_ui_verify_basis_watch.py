from playwright.sync_api import sync_playwright
import os
def run_cuj(page):
    page.route('**/api/data/derivatives/marketwatch*', lambda route: route.fulfill(status=200, content_type='application/json', body='{"data":{"RELIANCE":[{"symbol":"RELIANCE","trade_date":"2026-05-25","instrument_type":"FUTSTK","expiry":"2026-06-25","strike_price":0.0,"option_type":"XX","open_price":3000.0,"high_price":3000.0,"low_price":3000.0,"close_price":3000.0,"settle_price":3000.0,"contracts":1000,"val_inlakh":100.0,"open_int":10000,"chg_in_oi":100,"date":"2026-06-25","price":3000.0,"vol":1000,"atp":3000.0,"oi":10000,"dte":31,"bps":0.0,"yield":0.0}]}}'))
    page.route('**/api/data/derivatives/marketwatch', lambda route: route.fulfill(status=200, content_type='application/json', body='{"data":{"RELIANCE":[{"symbol":"RELIANCE","trade_date":"2026-05-25","instrument_type":"FUTSTK","expiry":"2026-06-25","strike_price":0.0,"option_type":"XX","open_price":3000.0,"high_price":3000.0,"low_price":3000.0,"close_price":3000.0,"settle_price":3000.0,"contracts":1000,"val_inlakh":100.0,"open_int":10000,"chg_in_oi":100,"date":"2026-06-25","price":3000.0,"vol":1000,"atp":3000.0,"oi":10000,"dte":31,"bps":0.0,"yield":0.0}]}}'))
    page.goto('http://localhost:8000/workbench')
    page.wait_for_timeout(1000)
    try:
        page.click('text=Basis Watch')
        page.fill('#custom-symbol-input', 'RELIANCE')
        page.click('button[onclick=\'addCustomSymbol()\']')
        page.wait_for_timeout(3000)
        os.makedirs('/home/jules/verification/screenshots', exist_ok=True)
        page.screenshot(path='/home/jules/verification/screenshots/reliance_basis_watch.png')
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
