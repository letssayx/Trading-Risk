from playwright.sync_api import sync_playwright
import time

def verify_workbench():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to Workbench
        page.goto("http://localhost:8000/workbench")
        time.sleep(2) # Wait for load

        # 1. Verify Risk Dashboard (Left Panel)
        print("Verifying Risk Dashboard...")
        page.wait_for_selector(".risk-gauge-container")
        page.screenshot(path="verification/1_risk_dashboard.png")

        # 2. Verify Trade Book (Bottom Panel)
        print("Verifying Trade Book...")
        page.wait_for_selector("#tradeBookTable")
        # Test Sort
        page.click("th:has-text('Symbol')")
        time.sleep(0.5)
        page.screenshot(path="verification/2_trade_book.png")

        # 3. Verify Report Modal
        print("Verifying Report Modal...")
        page.click("text=Reports")
        page.wait_for_selector("#report-modal", state="visible")
        page.screenshot(path="verification/3_report_modal.png")
        page.click("text=✕") # Close modal

        # 4. Verify Jules Chat (Right Panel Tab)
        print("Verifying Jules Chat...")
        page.click("text=🤖 Jules")
        page.wait_for_selector("#chat-input")
        page.fill("#chat-input", "Create a Z-Score filter")
        page.click("text=➤")
        time.sleep(1) # Wait for stub response
        page.screenshot(path="verification/4_jules_chat.png")

        # 5. Verify Layout Manager
        print("Verifying Layout Manager...")
        page.hover("text=View")
        page.wait_for_selector(".dropdown-content", state="visible")
        page.screenshot(path="verification/5_layout_manager.png")

        browser.close()
        print("Verification Complete. Screenshots saved in verification/")

if __name__ == "__main__":
    verify_workbench()
