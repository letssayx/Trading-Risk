from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("http://localhost:8000/workbench")
    page.evaluate("switchMainTab('derivatives')")
    page.evaluate("switchDerivTab('fii')")
    page.wait_for_timeout(2000)

    print("Executing loadFiiAnalysis(new Event())...")
    page.evaluate("""
        loadFiiTrendChart(new Event('change'));
    """)
    page.wait_for_timeout(2000)

    browser.close()
