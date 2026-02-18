from playwright.sync_api import sync_playwright, expect
import os
import time

def test_data_viewer_fix():
    print("Starting Playwright verification...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Navigate to Workbench
        try:
            page.goto("http://localhost:8000/workbench")
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            return

        # Wait for page to be ready
        page.wait_for_load_state("networkidle")

        # 2. Check Autocomplete on API Key (Config Modal)
        # Open Config Modal
        page.click("text=Config")
        page.wait_for_selector("#config-modal", state="visible")

        api_input = page.locator("#api-key-input")
        attr = api_input.get_attribute("autocomplete")
        print(f"API Key Autocomplete: {attr}")
        if attr != "off":
             print("❌ Verification Failed: API Key autocomplete is not 'off'")
        else:
             print("✅ API Key autocomplete is correct")

        # Close Config Modal
        page.click("#config-modal .close")

        # 3. Open Data Viewer
        page.click("text=Data Viewer")
        page.wait_for_selector("#data-viewer-modal", state="visible")

        # 4. Check Autocomplete on Symbol
        symbol_input = page.locator("#view-symbol")
        attr = symbol_input.get_attribute("autocomplete")
        print(f"Symbol Input Autocomplete: {attr}")
        if attr != "off":
             print("❌ Verification Failed: Symbol autocomplete is not 'off'")
        else:
             print("✅ Symbol autocomplete is correct")

        # 5. Test Data Loading (Fix verification)
        # Enter Date and Symbol
        page.fill("#view-date", "2026-02-19")
        page.fill("#view-symbol", "RELIANCE")

        # Click Load Data
        page.click("#data-viewer-modal button:has-text('Load Data')")

        # 6. Wait for response
        try:
            time.sleep(2) # Simple wait for demo

            content = page.locator("#data-view-results").inner_text()
            print(f"Result Content: {content}")

            if "Error loading data" in content and "Unexpected token" in content:
                 print("❌ Verification Failed: Server 500 Error detected.")
            elif "No data found" in content:
                 print("✅ Verification Passed: 'No data found' received (Expected for empty DB).")
            elif "Found" in content:
                 print("✅ Verification Passed: Data found.")
            else:
                 print(f"⚠️ Unexpected state: {content}")

        except Exception as e:
            print(f"⚠️ Error waiting for results: {e}")

        # Close Data Viewer
        page.click("#data-viewer-modal .close")
        page.wait_for_selector("#data-viewer-modal", state="hidden")

        # 7. Test Upload Modal Close (Fix verification)
        page.click("text=Import Data")
        page.wait_for_selector("#bhavcopy-upload-modal", state="visible")

        # Click the close button
        # This will verify if the listener is attached correctly to THIS modal's close button
        page.click("#bhavcopy-upload-modal .close")
        try:
            page.wait_for_selector("#bhavcopy-upload-modal", state="hidden", timeout=2000)
            print("✅ Upload Modal closed via 'X' button")
        except:
            print("❌ Verification Failed: Upload Modal did not close via 'X' button")

        # 8. Take Screenshot
        if not os.path.exists("verification"):
            os.makedirs("verification")
        page.screenshot(path="verification/verification.png")
        print("📸 Screenshot saved to verification/verification.png")

        browser.close()

if __name__ == "__main__":
    test_data_viewer_fix()
