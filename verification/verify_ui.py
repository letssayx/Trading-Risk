from playwright.sync_api import sync_playwright
import time

def verify_workbench():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to Workbench
        page.goto("http://localhost:8000/workbench")
        time.sleep(2) # Wait for load

        # 1. Verify Risk Dashboard (Top Row - NEW STRUCTURE)
        print("Verifying Risk Dashboard...")
        # New structure uses specific class .risk-card
        page.wait_for_selector(".risk-card")
        page.screenshot(path="verification/1_risk_dashboard_restored.png")

        # 2. Verify Trade Book (Bottom Panel)
        print("Verifying Trade Book...")
        page.wait_for_selector(".bottom-panel")
        page.screenshot(path="verification/2_trade_book_restored.png")

        # 3. Verify Spread Builder (Left Panel)
        print("Verifying Spread Builder...")
        page.wait_for_selector(".left-panel")
        page.screenshot(path="verification/3_spread_builder_restored.png")

        # 4. Verify Jules Chat (Right Panel)
        print("Verifying Jules Chat...")
        # Check for tab button
        if page.is_visible("button[data-tab='jules']"):
            page.click("button[data-tab='jules']")
            time.sleep(0.5)
        page.wait_for_selector("#julesTab")
        page.screenshot(path="verification/4_jules_chat_restored.png")

        browser.close()
        print("Verification Complete. Screenshots saved in verification/")

if __name__ == "__main__":
    verify_workbench()
