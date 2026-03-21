from playwright.sync_api import sync_playwright, expect
import time

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("Fetching title and headers for /")
        page.goto("http://localhost:8000/")
        page.wait_for_timeout(1000)
        print(f"Title: {page.title()}")

        print("Fetching title and headers for /ui")
        response = page.goto("http://localhost:8000/ui")
        page.wait_for_timeout(1000)
        print(f"Status: {response.status}")
        print(f"Title: {page.title()}")
        print("Snippets:")
        print(page.content()[:500])

        context.close()
        browser.close()
        print("Done.")

if __name__ == "__main__":
    verify_ui()
