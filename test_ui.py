import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Ensure our mock python backend is running
        await page.goto("http://localhost:8000/chat")
        await page.wait_for_selector(".main-chat")
        await page.wait_for_selector(".sidebar")

        # Take a screenshot to verify layout
        await page.screenshot(path="/tmp/chat_layout_fixed.png")
        await browser.close()

asyncio.run(main())
