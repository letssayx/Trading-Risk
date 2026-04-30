from playwright.sync_api import sync_playwright
import time

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8000/workbench")

        # Open special situations arb tab
        page.evaluate("switchMainTab('special_arb')")
        time.sleep(1)

        # Set symbol and load
        page.locator("#bb-symbol").fill("WIPRO")
        page.evaluate("syncBuybackHoldings(new Event('click'))")
        time.sleep(2)
        page.evaluate("syncBuybackPrices(new Event('click'))")
        time.sleep(2)

        # Let's set some custom values to ensure future profit is negative
        # CMP is say 400. Buyback is 500. Future is 390.
        # Actually in buyback arb, you BUY cash (at 400) and SHORT future (at 390).
        # Profit on future = (futPrice - CMP) = 390 - 400 = -10 (loss)

        page.locator("#bb-cmp").fill("400")
        page.locator("#bb-fut-price").fill("390")
        page.locator("#bb-price").fill("500")
        page.locator("#bb-total-offer").fill("1000000")
        page.evaluate("calculateBuyback()")

        page.screenshot(path="/home/jules/verification/screenshots/buyback_custom.png", full_page=True)
        browser.close()

verify_ui()
