from playwright.sync_api import sync_playwright
import time

def verify_jules_integration():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8000/workbench")
        time.sleep(2)

        # 1. Verify Layout Elements
        print("Verifying Layout...")
        page.wait_for_selector(".risk-panel")

        # 2. Interact with Jules Chat
        # In the NEW layout (ASCII based), Jules Chat is STATICALLY VISIBLE in the right panel.
        # There are NO TABS for Python/Jules in the updated HTML structure I wrote earlier.
        # The structure is:
        # <div class="right-panel">
        #    <div class="right-header">PYTHON CONSOLE</div> ...
        #    <div class="right-header">JULES CHAT</div> ...
        # </div>
        # So I don't need to click a tab button.

        print("Testing Jules Chat...")
        page.wait_for_selector("#chat-input")

        # Send a Strategy Request
        page.fill("#chat-input", "Create Turtle strategy with Z-Score filter")
        page.press("#chat-input", "Enter")

        # 3. Verify Response
        print("Waiting for Jules Response...")
        try:
            page.wait_for_selector(".code-block", timeout=10000)
            print("Code Block Generated!")
        except Exception:
            print("Code Block NOT found within timeout.")
            page.screenshot(path="verification/jules_fail.png")
            raise

        # 4. Verify Run Button
        print("Checking Run Button...")
        page.wait_for_selector("button:has-text('RUN')")

        # 5. Verify Visualization in Composer
        # I added the Strategy Map button in the previous step.
        # Let's click it to show the canvas.
        print("Switching to Strategy Map...")
        page.click("button:has-text('Strategy Map')")
        time.sleep(0.5)

        print("Checking Strategy Composer Visualization...")
        page.wait_for_selector("#composer-canvas .node")
        print("Strategy Nodes Visualized!")

        page.screenshot(path="verification/jules_integration_success.png")
        print("Integration Verification Complete.")
        browser.close()

if __name__ == "__main__":
    verify_jules_integration()
