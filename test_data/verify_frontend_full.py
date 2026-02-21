from playwright.sync_api import sync_playwright, expect

def test_workbench(page):
    print("Navigating to Workbench...")
    page.goto("http://127.0.0.1:8000/workbench")

    # 1. Verify Title
    expect(page).to_have_title("Turtle Terminal - Trader Workbench")
    print("✅ Title Verified")

    # 2. Verify Data Viewer Link
    # It opens in new tab, so we need to catch the popup or just check href
    # But it's an onclick with window.open.
    # We can check if the element exists.
    viewer_btn = page.get_by_text("Data Viewer")
    expect(viewer_btn).to_be_visible()
    print("✅ Data Viewer Link Verified")

    # 3. Verify Jules Chat Scroll
    # Add many messages to force scroll
    # This is hard to verify visually via script without taking screenshot before/after and comparing scroll position.
    # We'll just verify the container exists.
    expect(page.locator("#jules-content")).to_have_css("overflow-y", "auto")
    print("✅ Jules Chat Scroll Verified (CSS)")

    # 4. Verify Import Modal Renaming
    page.get_by_text("Import Data").click()
    expect(page.locator("label", has_text="Cash (CM)")).to_be_visible()
    expect(page.locator("label", has_text="F&O (Derivatives)")).to_be_visible()
    print("✅ Import Labels Verified")

    # Close Import
    page.keyboard.press("Escape")

    # Take Screenshot
    page.screenshot(path="/home/jules/verification/workbench_final.png")
    print("📸 Screenshot taken")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        try:
            test_workbench(page)
        except Exception as e:
            print(f"❌ Test Failed: {e}")
            raise e
        finally:
            browser.close()
