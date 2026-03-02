from playwright.sync_api import sync_playwright
import json

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        api_responses = {}

        def on_response(response):
            if "api/" in response.url and "corporate" in response.url:
                try:
                    data = response.json()
                    print(f"\nAPI Hit: {response.url}")
                    if isinstance(data, dict) and 'data' in data:
                        dlist = data['data']
                        if dlist:
                            print(f"  Length: {len(dlist)}")
                            stages = set(x.get('stage', 'No Stage') for x in dlist if isinstance(x, dict))
                            print(f"  Stages: {stages}")
                except Exception as e:
                    pass

        page.on("response", on_response)

        # 1. Load root to get cookies
        page.goto("https://www.nseindia.com", wait_until="networkidle")

        # 2. Go to the Rights URL directly
        page.goto("https://www.nseindia.com/companies-listing/corporate-filings-rights", wait_until="networkidle")

        # 3. Wait to see if there is an In-Principle link that we can click.
        try:
            print("Looking for In-Principle tab...")
            # We look for any text matching 'In-Principle'
            locator = page.locator("a:has-text('In-Principle'), button:has-text('In-Principle')")
            if locator.count() > 0:
                print("Found tab. Clicking...")
                locator.first.click(timeout=5000)
                page.wait_for_timeout(5000)
            else:
                print("Could not find In-Principle tab text.")
                print(page.content()[:1000]) # just to debug what loaded
        except Exception as e:
            print("Error clicking:", e)

        browser.close()

run()
