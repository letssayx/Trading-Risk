import pytest
import os
import time
from playwright.sync_api import sync_playwright

def test_rollover_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Add console listener BEFORE goto
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser Error: {err}"))

        page.goto("http://localhost:8000/workbench", timeout=60000)

        # Click on derivatives analysis tab
        page.evaluate("switchMainTab('derivatives')")
        page.wait_for_timeout(1000)

        # Click on Rollover Analysis sub-tab
        page.evaluate("switchDerivTab('rollover')")
        page.wait_for_timeout(5000)  # Wait longer for data

        # Take screenshot
        page.screenshot(path="rollover_ui_check.png")

        browser.close()

if __name__ == "__main__":
    test_rollover_ui()