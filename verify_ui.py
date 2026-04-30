from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    # Click the Special Situations Arb tab
    page.evaluate("switchMainTab('special_arb')")
    page.wait_for_timeout(1000)

    # Load symbol "WIPRO"
    page.fill("#bb-symbol", "WIPRO")

    # Click Sync from Back End
    page.evaluate("document.querySelector('button[onclick*=\"syncBuybackPrices\"]').click()")
    page.wait_for_timeout(3000)

    # Click Sync for Shareholding Pattern
    page.evaluate("document.querySelector('button[onclick*=\"syncBuybackHoldings\"]').click()")
    page.wait_for_timeout(4000)

    # Set buyback price
    page.fill("#bb-price", "250")

    # Fill in Buy Back Offer shares from the image provided
    # According to image: 60,000,000
    page.fill("#bb-total-offer", "60000000")

    # Trigger oninput
    page.evaluate("calculateBuyback()")
    page.wait_for_timeout(1000)

    # Take screenshot of Buy Back form
    page.screenshot(path="/home/jules/verification/screenshots/buyback_full.png", full_page=True)
    page.wait_for_timeout(2000)

if __name__ == "__main__":
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
