from playwright.sync_api import sync_playwright

def run_cuj(page):
    # Navigate to the main workbench
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(3000)

    # We need to click on "Special Situation Arb" tab
    page.locator('.main-tab[data-target="special_arb"]').click()
    page.wait_for_timeout(1000)

    # Take a screenshot to show the buyback UI is there and doesn't crash on load
    page.screenshot(path="/home/jules/verification/screenshots/special_arb_buyback.png")
    page.wait_for_timeout(500)

    # Click OFS sub-tab
    page.locator('#ss-tab-btn-ofs').click()
    page.wait_for_timeout(1000)

    # Enter some numbers in OFS
    page.locator('#ofs-promoter').fill("100000")
    page.locator('#ofs-fii').fill("50000")
    page.locator('#ofs-retail').fill("20000")
    page.locator('#ofs-total-offer').fill("10000")
    page.locator('#ofs-price').fill("100")
    page.locator('#ofs-cmp').fill("110")
    page.wait_for_timeout(1000)

    # Take screenshot of OFS
    page.screenshot(path="/home/jules/verification/screenshots/special_arb_ofs.png")
    page.wait_for_timeout(1000)

    # Also check Fundamental Analysis to make sure it's not a blank screen
    page.locator('.main-tab[data-target="fundamentals"]').click()
    page.wait_for_timeout(1000)

    page.screenshot(path="/home/jules/verification/screenshots/fundamentals_tab.png")
    page.wait_for_timeout(1000)


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
