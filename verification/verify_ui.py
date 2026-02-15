from playwright.sync_api import sync_playwright
import time

def verify_workbench():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture Console Logs
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"BROWSER ERROR: {exc}"))

        # Navigate to Workbench
        try:
            page.goto("http://localhost:8000/workbench")
            time.sleep(2) # Wait for load

            # 1. Verify Risk Dashboard (Top Row)
            print("Verifying Risk Dashboard...")
            page.wait_for_selector(".metric-card:has-text('Risk Scorecard')")
            page.screenshot(path="verification/1_risk_dashboard_restored.png")

            # 2. Verify Trade Book (Bottom Row)
            print("Verifying Trade Book...")
            # Ensure JS injected the table
            page.wait_for_selector("#tradeBookTable")
            page.screenshot(path="verification/2_trade_book_restored.png")

            # 3. Verify Spread Builder (Left Panel)
            print("Verifying Spread Builder...")
            page.wait_for_selector(".spread-builder-container")
            page.screenshot(path="verification/3_spread_builder_restored.png")

            # 4. Verify Jules Chat (Right Panel)
            print("Verifying Jules Chat...")
            if page.is_visible("button:has-text('🤖 Jules')"):
                page.click("button:has-text('🤖 Jules')")
                time.sleep(0.5)
            page.wait_for_selector("#chat-history")
            page.screenshot(path="verification/4_jules_chat_restored.png")

            print("Verification Complete.")
        except Exception as e:
            print(f"VERIFICATION FAILED: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_workbench()
