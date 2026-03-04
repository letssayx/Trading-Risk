import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        print("Navigating to http://127.0.0.1:8000/workbench")
        try:
            await page.goto("http://127.0.0.1:8000/workbench", wait_until="networkidle")

            # Switch to AI-Analyze tab by clicking its button directly with evaluate
            print("Switching to AI-Analyze tab...")
            await page.evaluate("openMainTab(new Event('click'), 'tab-ai_analyze')")

            # Wait for content to render
            await page.wait_for_selector('.ai-analysis-feed', state='attached', timeout=5000)

            # Simulate running AI analysis to show the feed
            await page.evaluate("document.getElementById('ai-analysis-feed').style.display = 'flex';")

            # Take screenshot of AI tab
            screenshot_path = "ai_tab_hidden_engines.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())