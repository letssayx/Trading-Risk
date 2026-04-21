from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    print("Clicking Derivatives Analysis Tab...")
    page.locator("text='Derivatives Analysis'").click()
    page.wait_for_timeout(2000)

    print("Clicking Macro Tracker Tab using JS...")
    # Using specific class names and ID from the DOM
    page.evaluate("""
        var tab = document.getElementById('deriv-tab-btn-macro');
        if(tab) {
            tab.click();
        } else {
            console.log('Macro tab not found');
        }
    """)
    page.wait_for_timeout(2000)

    page.screenshot(path="macro_tracker_initial.png")

    print("Clicking Sync Data Button...")
    page.evaluate("""
        var btn = document.getElementById('macro-sync-btn');
        if(btn) {
            btn.click();
        } else {
            console.log('Sync button not found');
        }
    """)
    page.wait_for_timeout(5000) # Wait for sync

    print("Saving screenshot...")
    page.screenshot(path="macro_tracker_synced.png")
    page.wait_for_timeout(2000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="verification_videos",
            viewport={"width": 1400, "height": 800}
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
