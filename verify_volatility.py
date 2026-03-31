from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("http://127.0.0.1:8000/workbench")
        page.wait_for_timeout(2000)

        # Switch to Derivatives Analysis tab
        page.evaluate("switchMainTab('derivatives')")
        page.wait_for_timeout(1000)

        # Switch to Volatility Analysis tab
        page.evaluate("switchDerivTab('optanalysis')")
        page.wait_for_timeout(1000)

        # Click Load Volatility
        print("Clicking Load Volatility...")
        page.evaluate("document.querySelector('#deriv-tab-optanalysis button').click()")

        # Wait for charts to load
        page.wait_for_timeout(5000)

        page.screenshot(path="volatility_analysis_loaded.png", full_page=True)
        print("Screenshot saved to volatility_analysis_loaded.png")

        # Download CSV
        page.evaluate("""
            const btns = document.querySelectorAll('#deriv-tab-optanalysis button');
            for (let btn of btns) {
                if (btn.innerText.includes('CSV')) {
                    btn.click();
                    break;
                }
            }
        """)
        page.wait_for_timeout(2000)

        browser.close()

run()