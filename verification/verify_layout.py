from playwright.sync_api import sync_playwright
import time

def verify_layout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8000/workbench")
        time.sleep(2)

        # 1. Check Risk Panel (Left)
        print("Checking Risk Panel...")
        page.wait_for_selector(".risk-panel")
        page.wait_for_selector("text=Risk Panel (Critical)")

        # 2. Check Strategy Ribbon
        print("Checking Strategy Ribbon...")
        page.wait_for_selector(".strategy-ribbon")
        page.wait_for_selector("button:has-text('Turtle')")

        # 3. Check Right Panel (Python/Jules)
        print("Checking Right Panel...")
        page.wait_for_selector(".right-panel")
        page.wait_for_selector("text=PYTHON CONSOLE")
        page.wait_for_selector("text=JULES CHAT")

        # 4. Check Trade Book
        print("Checking Trade Book...")
        page.wait_for_selector(".trade-book")
        page.wait_for_selector("#tradeBookTable")

        # Screenshot
        page.screenshot(path="verification/layout_check.png")
        print("Layout Verified.")
        browser.close()

if __name__ == "__main__":
    verify_layout()
