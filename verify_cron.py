import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        page.on("console", lambda msg: print(f"Browser console: {msg.type} {msg.text}"))

        await page.goto("http://localhost:8000")

        # Click the Corporate Data tab
        await page.click("text=Corporate Data")
        await page.wait_for_timeout(1000)

        # Find Cron Settings button
        print("Clicking Cron Settings...")

        # the button has id 'cron-settings-btn'
        await page.click("#cron-settings-btn")

        # Wait a moment for modal to appear
        await page.wait_for_timeout(2000)

        # Take a screenshot
        await page.screenshot(path="/home/jules/verification/screenshots/verification6.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
