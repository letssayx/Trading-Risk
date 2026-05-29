const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log("Navigating to local server...");

  try {
      await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
      console.log("Navigated.");
      await page.screenshot({ path: 'home.png' });
  } catch (e) {
      console.log("Page didn't fully load, but that's expected without data:", e.message);
  }

  await browser.close();
  console.log("Done");
})();
