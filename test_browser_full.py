from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    page.on("console", lambda msg: print(f"Browser console [{msg.type}]: {msg.text}"))
    page.on("pageerror", lambda err: print(f"Browser error: {err}"))

    print("Switching to derivatives")
    page.evaluate("switchMainTab('derivatives')")
    page.wait_for_timeout(1000)

    print("Switching to Market Activity")
    page.evaluate("switchDerivTab('market')")
    page.wait_for_timeout(2000)
    page.evaluate("loadMarketActivity()")
    page.wait_for_timeout(5000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        run_cuj(page)
        browser.close()
