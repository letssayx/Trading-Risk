const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();

    try {
        await page.goto('http://127.0.0.1:8000/workbench');

        await page.waitForTimeout(4000);

        await page.click('text=Derivatives Analysis');
        await page.waitForTimeout(2000);
        await page.click('text=Rollover Analysis');
        await page.waitForTimeout(2000);

        // Click master sync at the top right to populate data
        const syncButton = await page.locator('button:has-text("Master Sync")');
        if (await syncButton.isVisible()) {
            await syncButton.click();
            await page.waitForTimeout(15000); // wait for global sync to fetch data
        } else {
             console.log("Master Sync not found");
        }

        await page.screenshot({ path: '/home/jules/verification/rollover_styled_5.png', fullPage: true });
        console.log('Successfully captured screenshot of Rollover Analysis with styling.');

    } catch (e) {
        console.error('Test failed:', e);
    } finally {
        await context.close();
        await browser.close();
    }
})();
