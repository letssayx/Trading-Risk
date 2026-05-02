from playwright.sync_api import sync_playwright

def run_test(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    # Check Special Situation Arb tabs order
    page.evaluate("switchMainTab('special_arb')")
    page.wait_for_timeout(1000)

    # Screenshot the Special Situation Arb view
    page.screenshot(path="/home/jules/verification/screenshots/verification2.png", full_page=True)
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        try:
            run_test(page)
        finally:
            context.close()
            browser.close()
