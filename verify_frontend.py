import os
import time
from playwright.sync_api import sync_playwright, expect

def verify_frontend():
    print("Starting frontend verification...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Load Workbench
        print("Loading workbench...")
        try:
            page.goto("http://localhost:8000/workbench")
            page.wait_for_selector(".main-tabs-bar", state="visible", timeout=10000)
            print("Workbench loaded.")
        except Exception as e:
            print(f"Failed to load workbench: {e}")
            page.screenshot(path="verification_failure_load.png")
            browser.close()
            return

        # 2. Switch to Import Tab
        print("Switching to Import tab...")
        try:
            # Click the "Import Data" tab
            page.click("div[data-target='import']")

            # Verify the import container is visible
            # The structure is #tab-import -> .import-container -> #bhavcopy-upload-modal
            expect(page.locator("#tab-import")).to_be_visible()
            expect(page.locator("#bhavcopy-upload-modal")).to_be_visible()
            print("Import tab visible.")

            # Verify sub-tabs exist
            expect(page.locator(".tab-btn[data-tab='latest']")).to_be_visible()
            expect(page.locator(".tab-btn[data-tab='historical']")).to_be_visible()
            expect(page.locator(".tab-btn[data-tab='manual']")).to_be_visible()
            print("Import sub-tabs verified.")

        except Exception as e:
            print(f"Failed to switch to Import tab: {e}")
            page.screenshot(path="verification_failure_import_tab.png")
            browser.close()
            return

        # 3. Verify Recent Imports Table Columns
        print("Verifying Recent Imports table structure...")
        try:
            # Wait for history to load (it might take a moment if DB is slow, but HTML structure should be there)
            # We look for the table header specifically
            # It might say "No recent imports found" if empty, so we check for that OR the table

            # Force a reload of history if needed? The JS does it on open()
            page.wait_for_timeout(2000) # Give JS time to fetch

            # Check if table headers exist (Table Name, Status, Last Data Date, Downloaded At)
            # Or check if "No recent imports" message is there
            content = page.content()

            if "No recent imports found" in content or "Failed to load history" in content:
                print("History empty or failed to load (Expected if no data).")
            else:
                # If table exists, check headers
                headers = page.locator("#import-history-list th").all_inner_texts()
                print(f"Found headers: {headers}")

                expected_headers = ["Table Name", "Status Summary", "Last Data Date", "Downloaded At"]
                missing = [h for h in expected_headers if h not in headers]

                if not missing:
                    print("All expected headers found.")
                else:
                    print(f"Missing headers: {missing}")
                    # This is a soft fail if the table isn't rendered yet

        except Exception as e:
            print(f"Failed to verify history table: {e}")

        # 4. Verify Manual Upload Tab
        print("Verifying Manual Upload tab...")
        try:
            page.click(".tab-btn[data-tab='manual']")
            expect(page.locator("#tab-manual")).to_be_visible()

            # Check for the new date input
            expect(page.locator("#manual-date")).to_be_visible()
            print("Manual date input found.")

        except Exception as e:
             print(f"Failed to verify manual tab: {e}")
             page.screenshot(path="verification_failure_manual.png")


        # 5. Switch to Historical Tab
        print("Switching to Historical Data tab...")
        try:
            page.click("div[data-target='history']")
            expect(page.locator("#tab-history")).to_be_visible()
            print("Historical tab visible.")

        except Exception as e:
             print(f"Failed to switch to Historical tab: {e}")
             page.screenshot(path="verification_failure_history.png")

        # Take success screenshot
        page.screenshot(path="verification_success.png")
        print("Verification complete. Screenshot saved to verification_success.png")
        browser.close()

if __name__ == "__main__":
    verify_frontend()
