const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ recordVideo: { dir: '/home/jules/verification/videos/' } });
  const page = await context.newPage();

  await page.goto('http://localhost:8000/workbench'); // Use correct URL path!

  // Wait a bit for JS to render tabs
  await page.waitForTimeout(2000);

  // Click first text=Derivatives Analysis
  await page.click('text="Derivatives Analysis"');

  // Try clicking by class or ID
  await page.click('#deriv-tab-btn-rollover', { force: true });

  // Wait for the matrix to load
  await page.waitForTimeout(5000); // Give it time to attempt fetch

  // Select a symbol for the top chart
  await page.fill('#rollover-symbol', 'NIFTY', { force: true }).catch(e => console.log("Fill err:", e));
  await page.evaluate(() => {
     if(window.RolloverTool) {
        document.getElementById('rollover-symbol').value = 'NIFTY';
        window.RolloverTool.analyzeSingle();
     }
  });

  await page.waitForTimeout(5000);

  await page.screenshot({ path: '/home/jules/verification/screenshots/verification3.png', fullPage: true });

  await browser.close();
})();
