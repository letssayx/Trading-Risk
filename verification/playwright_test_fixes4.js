const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({
        viewport: { width: 1920, height: 1080 }
    });

    try {
        await page.goto('http://127.0.0.1:8000/workbench');
        await page.waitForTimeout(2000);
        await page.evaluate("switchMainTab('derivatives')");
        await page.waitForTimeout(1000);
        await page.evaluate("switchDerivTab('oi')");
        await page.waitForTimeout(2000);

        // Take a full page screenshot
        const tabContent = await page.$('#deriv-tab-oi');
        await tabContent.screenshot({ path: 'verification/screenshots/oi_analysis_full.png' });
    } catch (e) {
        console.error("Test failed:", e);
    } finally {
        await browser.close();
    }
})();
