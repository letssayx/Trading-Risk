from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(1000)

    # Click the "Special Sit" tab in the left sidebar
    page.get_by_text("Special Sit").click()
    page.wait_for_timeout(1000)

    # Click "Dividends Databank" sub tab if not already open
    page.get_by_role("button", name="Dividends Data Bank").click()
    page.wait_for_timeout(2000)

    # Let's take a screenshot of the main table.
    page.screenshot(path="/home/jules/verification/screenshots/verification.png")
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
            run_cuj(page)
        finally:
            context.close()  # MUST close context to save the video
            browser.close()
