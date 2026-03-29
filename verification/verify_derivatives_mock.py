import asyncio
import json
from playwright.async_api import async_playwright

async def handle_route(route):
    # Mock option chain data to render the Highest OI chart
    if "api/data/derivatives/option_chain?symbol=NIFTY" in route.request.url:
        mock_data = {
            "data": [
                {"strike": 22000, "ce_oi": 50000, "pe_oi": 20000, "expiry": "2024-05-30"},
                {"strike": 22100, "ce_oi": 60000, "pe_oi": 30000, "expiry": "2024-05-30"},
                {"strike": 22200, "ce_oi": 75000, "pe_oi": 45000, "expiry": "2024-05-30"},
                {"strike": 22300, "ce_oi": 120000, "pe_oi": 55000, "expiry": "2024-05-30"},
                {"strike": 22400, "ce_oi": 80000, "pe_oi": 110000, "expiry": "2024-05-30"},
                {"strike": 22500, "ce_oi": 40000, "pe_oi": 90000, "expiry": "2024-05-30"},
                {"strike": 22600, "ce_oi": 20000, "pe_oi": 70000, "expiry": "2024-05-30"}
            ],
            "spot_price": 22350
        }
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(mock_data))
    elif "api/data/derivatives/pcr_history" in route.request.url:
        mock_data = {
            "dates": ["2024-05-01", "2024-05-02", "2024-05-03", "2024-05-04", "2024-05-05"],
            "total_oi": [10000, 11000, 10500, 12000, 11500],
            "price": [22000, 22100, 22050, 22200, 22150],
            "pcr": [0.8, 0.9, 0.85, 0.95, 0.9]
        }
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(mock_data))
    else:
        await route.continue_()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.route("**/*", handle_route)

        print("Navigating to workbench...")
        await page.goto("http://localhost:8000/workbench")

        await page.click("text=Derivatives Analysis")
        await page.wait_for_timeout(1000)

        print("Checking OI Analysis...")
        await page.click("text=OI Analysis")
        await page.wait_for_timeout(1000)

        await page.fill("#opt-analysis-symbol", "NIFTY")

        # Click the "Load Charts" button inside the right-side layout block
        await page.evaluate("document.querySelector('button[onclick=\"loadOptionsAnalysis()\"]').click();")

        await page.wait_for_timeout(3000)

        await page.screenshot(path="/home/jules/verification/screenshots/oi_analysis_mocked_final.png", full_page=True)
        print("Done!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
