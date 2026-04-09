from playwright.sync_api import sync_playwright
import time

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    print("Clicking derivatives tab...")
    page.evaluate("document.querySelector('.main-tab[data-target=\"derivatives\"]').click()")
    page.wait_for_timeout(1000)

    print("Clicking tools item tab...")
    page.evaluate("document.querySelector('#deriv-tab-btn-oi').click()")
    page.wait_for_timeout(1000)

    print("Clicking refresh explicitly...")
    page.evaluate("document.querySelector('button[onclick=\"OiTool.loadAggregatedData(true)\"]').click()")
    page.wait_for_timeout(5000)

    page.screenshot(path="/home/jules/verification/screenshots/oi_table.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
