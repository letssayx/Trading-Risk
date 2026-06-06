from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:3000/templates/workbench.html")
    page.wait_for_timeout(2000)

    # We click the tabs using playwright elements directly instead of injecting JS
    page.evaluate("document.querySelector('.main-tab[data-target=\"derivatives\"]').click()")
    page.wait_for_timeout(1000)

    # Make sure we actually are in Derivatives Analysis
    page.evaluate("document.querySelectorAll('.main-tab-content').forEach(el => el.classList.remove('active'))")
    page.evaluate("document.getElementById('tab-derivatives').classList.add('active')")

    # Make sure the Market Analysis tab is selected and shown
    page.evaluate("document.querySelectorAll('.deriv-sub-tab').forEach(el => { el.style.display = 'none'; el.classList.remove('active'); })")
    page.evaluate("document.getElementById('deriv-tab-fii').style.display = 'block'")
    page.evaluate("document.getElementById('deriv-tab-fii').classList.add('active')")

    # Make sure we activate the tab button visually
    page.evaluate("document.querySelectorAll('.wb-tab').forEach(el => el.classList.remove('active'))")
    page.evaluate("document.getElementById('deriv-tab-btn-fii').classList.add('active')")
    page.wait_for_timeout(3000)

    # Take screenshot of the new Market Analysis tab with fixed block layout
    page.screenshot(path="/home/jules/verification/screenshots/verification6.png", full_page=True)
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
