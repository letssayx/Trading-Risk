from playwright.sync_api import sync_playwright

def run_cuj(page):
    # Navigate to the main workbench
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    # Click the Derivatives Analysis tab
    page.locator('.main-tab[data-target="derivatives"]').click()
    page.wait_for_timeout(2000)

    # Click the OI Analysis sub-tab
    page.locator('#deriv-tab-btn-oi').click()
    page.wait_for_timeout(2000)

    page.fill("#opt-analysis-symbol", "NIFTY")
    page.evaluate("document.getElementById('btn-load-options-analysis').disabled = false;")
    page.locator("#btn-load-options-analysis").click(force=True)
    page.wait_for_timeout(4000)

    # Scroll down to PCR history to ensure render without crash
    page.evaluate("document.getElementById('opt-analysis-pcr-chart').scrollIntoView({behavior: 'instant'})")
    page.wait_for_timeout(2000)

    page.screenshot(path="/home/jules/verification/screenshots/verification3.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            viewport={'width': 1280, 'height': 1024}
        )
        page = context.new_page()
        try:
            run_cuj(page)
            print("Finished Verification script.")
        except Exception as e:
            print(f"Error during execution: {e}")
            page.screenshot(path="/home/jules/verification/screenshots/error.png")
        finally:
            context.close()  # MUST close context to save the video
            browser.close()
