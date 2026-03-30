const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
    console.log("Starting verification...");
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        recordVideo: {
            dir: 'verification/videos/',
            size: { width: 1280, height: 720 }
        }
    });
    const page = await context.newPage();

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
                fii_opt_idx: [100000, 110000, 120000],
                fii_opt_stk: [5000, 6000, 7000],
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

        // Memory states that native JS tab switching must be used for workbench tabs
        console.log("Switching main tab to derivatives...");
        await page.evaluate("switchMainTab('derivatives')");
        await page.waitForTimeout(1000);

        // 1. Verify Nifty Chart / Market Activity Fixes
        console.log("Testing Market Activity...");
        await page.evaluate("switchDerivTab('market')");
        await page.waitForTimeout(2000);
        await page.screenshot({ path: 'verification/screenshots/market_activity_fixed.png' });

        // 2. Test Participant Dropdown Selection
        const selectBox = await page.$('#participant-type-select');
        if (selectBox) {
            console.log("Changing participant to Client...");
            await page.selectOption('#participant-type-select', 'Client');
            await page.waitForTimeout(1000);
            await page.screenshot({ path: 'verification/screenshots/participant_client_fixed.png' });
        } else {
            console.log("WARNING: Participant dropdown not found.");
        }

        // 3. Verify OI Search Box Behavior
        console.log("Testing OI Analysis Tab...");
        await page.evaluate("switchDerivTab('oi')");
        await page.waitForTimeout(2000);

        const oiSymbolLocator = page.locator('#oi-symbol');
        if (await oiSymbolLocator.count() > 0) {
            await page.fill('#oi-symbol', 'RELIANCE');
            await page.press('#oi-symbol', 'Enter');
            await page.waitForTimeout(1000);
            await page.screenshot({ path: 'verification/screenshots/oi_search_reliance.png' });

            console.log("Clearing OI Search...");
            await page.fill('#oi-symbol', '');
            await page.press('#oi-symbol', 'Backspace'); // simulate clear event
            await page.waitForTimeout(1000);
            await page.screenshot({ path: 'verification/screenshots/oi_cleared.png' });
        } else {
            console.log("Skipping OI tests, locator not found. This might be handled differently.");
        }

        console.log("Verification complete.");
    } catch (e) {
        console.error("Test failed:", e);
    } finally {
        await context.close();
        await browser.close();
    }
})();
