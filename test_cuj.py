from playwright.sync_api import sync_playwright

def run_cuj(page):
    print("Navigating to workbench...")
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    print("Opening Import Data tab...")
    page.get_by_text("Import Data", exact=True).click()
    page.wait_for_timeout(1000)

    # Check if "Contract Delta" is visible in latest section
    print("Checking Latest Section...")
    # Expand latest section
    page.locator(".tab-btn[data-tab='latest']").click()
    page.wait_for_timeout(1000)
    page.locator(".latest-type[value='contract_delta']").check(force=True)
    page.wait_for_timeout(1000)

    print("Checking Historical Range Section...")
    page.locator(".tab-btn[data-tab='historical']").click()
    page.wait_for_timeout(1000)
    page.locator(".range-type[value='contract_delta']").check(force=True)
    page.wait_for_timeout(1000)

    print("Checking Manual Upload Section...")
    page.locator(".tab-btn[data-tab='manual']").click()
    page.wait_for_timeout(1000)
    page.locator("#manual-type").select_option("contract_delta")
    page.wait_for_timeout(1000)

    print("Taking screenshot...")
    page.screenshot(path="/tmp/verification.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/tmp/videos")
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
