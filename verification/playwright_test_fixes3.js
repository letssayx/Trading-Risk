const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({
        viewport: { width: 1920, height: 1080 }
    });

    // Mock API requests for the specific tests to prevent DB dependencies locally
    await page.route('**/api/market-activity/cash-flow*', async route => {
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                dates: ["2026-03-20", "2026-03-21", "2026-03-22"],
                fii_net: [1000, -500, 2000],
                dii_net: [500, 1000, -100],
                nifty_close: [22000, 22100, 22200]
            })
        });
    });

    await page.route('**/api/market-activity/participant-oi*', async route => {
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                dates: ["2026-03-20", "2026-03-21", "2026-03-22"],
                fii_fut_idx: [50000, 55000, 60000],
                fii_fut_stk: [20000, 21000, 22000],
                fii_opt_idx_ce: [100000, 110000, 120000],
                fii_opt_stk_ce: [5000, 6000, 7000],
                fii_opt_idx_pe: [100000, 110000, 120000],
                fii_opt_stk_pe: [5000, 6000, 7000],
                dii_fut_idx: [-10000, -15000, -20000],
                pro_fut_idx: [1000, 2000, 3000],
                client_fut_idx: [-40000, -42000, -43000],
                nifty_close: [22000, 22100, 22200]
            })
        });
    });

    try {
        await page.goto('http://127.0.0.1:8000/workbench');
        await page.waitForTimeout(2000);
        await page.evaluate("switchMainTab('derivatives')");
        await page.waitForTimeout(1000);
        await page.evaluate("switchDerivTab('market')");
        await page.waitForTimeout(2000);

        // Wait for charts to render and get the full height
        await page.waitForTimeout(1000);

        // Take a full page screenshot by evaluating the height of the tab content
        const tabContent = await page.$('#deriv-tab-market');
        await tabContent.screenshot({ path: 'verification/screenshots/market_activity_full.png' });
    } catch (e) {
        console.error("Test failed:", e);
    } finally {
        await browser.close();
    }
})();
