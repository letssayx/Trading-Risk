from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    print("Testing Volatility Cone Colors...")
    page.evaluate("switchMainTab('derivatives')")
    page.wait_for_timeout(500)
    page.evaluate("switchDerivTab('optanalysis')")
    page.wait_for_timeout(500)

    # Render Vol Analysis Chart (the mock will intercept the volatility_cone call)
    page.evaluate("loadVolatilityAnalysis()")
    print("Waiting for chart to render...")

    # Wait for the chart to appear and UI to populate
    page.wait_for_timeout(5000)

    page.screenshot(path="/home/jules/verification/screenshots/vol_cone_colors.png", full_page=True)
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
