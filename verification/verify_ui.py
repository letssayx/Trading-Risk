from playwright.sync_api import sync_playwright

def run_cuj(page):
    # Navigate to the main application
    page.goto("http://localhost:8000/workbench")
    page.wait_for_timeout(2000)

    # Click on the "Derivatives Analysis" tab
    page.get_by_text("Derivatives Analysis", exact=True).click()
    page.wait_for_timeout(1000)

    # Click on the "Market Activity" sub-tab to test the new y1 axis fix and client net long color
    page.get_by_text("Market Activity", exact=True).click()
    page.wait_for_timeout(2000)
    page.screenshot(path="/home/jules/verification/screenshots/market_activity.png")

    # Click on "Adv Technicals" to test the Bloomberg theme and scrollability
    page.get_by_text("Adv Technicals", exact=True).click()
    page.wait_for_timeout(2000)

    # Scroll down to ensure the entire Echart is viewable
    page.evaluate("window.scrollBy(0, 500)")
    page.wait_for_timeout(1000)
    page.screenshot(path="/home/jules/verification/screenshots/adv_technicals.png")

    # Click on "OI Analysis" to check if the plot renders in its dedicated container
    page.get_by_text("OI Analysis", exact=True).click()
    page.wait_for_timeout(1000)
    page.locator("#oi-symbol").fill("NIFTY")
    page.get_by_role("button", name="Analyze").click()
    page.wait_for_timeout(2000)
    page.screenshot(path="/home/jules/verification/screenshots/oi_analysis.png")

    # Click on "Rollover Analysis" to check its dedicated container
    page.get_by_text("Rollover Analysis", exact=True).click()
    page.wait_for_timeout(1000)
    page.locator("#rollover-symbol").fill("RELIANCE")
    page.get_by_role("button", name="Analyze").click()
    page.wait_for_timeout(2000)
    page.screenshot(path="/home/jules/verification/screenshots/rollover_analysis.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            viewport={"width": 1280, "height": 800}
        )

        # We need to mock the API responses otherwise the charts might not render data and we can't fully verify visually

        # Mock Market Activity Cash Flow
        def mock_cash_flow(route):
            mock_data = {
                "dates": ["2023-10-01", "2023-10-02"],
                "fii_net": [1000, -500],
                "dii_net": [-200, 300],
                "nifty_close": [19500, 19600]
            }
            route.fulfill(json=mock_data)

        # Mock Market Activity Participant OI
        def mock_participant_oi(route):
            mock_data = {
                "dates": ["2023-10-01", "2023-10-02"],
                "fii_fut_idx": [50000, 48000],
                "fii_fut_stk": [10000, 12000],
                "fii_opt_idx": [20000, 25000],
                "fii_opt_stk": [5000, -2000],
                "pro_fut_idx": [10000, 12000],
                "client_fut_idx": [20000, 25000],
                "nifty_close": [19500, 19600]
            }
            route.fulfill(json=mock_data)

        # Mock Adv Technicals Dynamic Chart
        def mock_dynamic_chart(route):
            mock_data = {
                "dates": ["2023-10-01", "2023-10-02"],
                "ohlc": [[19000, 19100, 18900, 19050], [19050, 19200, 19000, 19150]],
                "ma20": [18950, 18970],
                "bb_upper_1": [19100, 19120], "bb_lower_1": [18800, 18820],
                "bb_upper_2": [19200, 19220], "bb_lower_2": [18700, 18720],
                "bb_upper_3": [19300, 19320], "bb_lower_3": [18600, 18620],
                "volume": [1000000, 1200000],
                "rsi_14": [55, 60],
                "macd": [10, 15],
                "macd_signal": [8, 12],
                "macd_hist": [2, 3],
                "total_oi": [5000000, 5200000],
                "iv": [12.5, 12.1],
                "pcr": [1.1, 1.2]
            }
            route.fulfill(json=mock_data)

        # Mock OI Analysis
        def mock_oi_analysis(route):
            mock_data = {
                "symbol": "NIFTY",
                "history": [
                    {"time": "2023-10-01", "price_chg_pct": 0.5, "oi_chg_pct": 2.0, "interpretation": "Long Build Up"},
                    {"time": "2023-10-02", "price_chg_pct": -0.2, "oi_chg_pct": -1.0, "interpretation": "Long Unwinding"}
                ]
            }
            route.fulfill(json=mock_data)

        # Mock Rollover Analysis
        def mock_rollover_analysis(route):
            mock_data = {
                "symbol": "RELIANCE",
                "trade_date": "2023-10-02",
                "rollover_pct": 65.5,
                "rollover_cost": 15.2,
                "rollover_cost_pct": 0.6,
                "near_month": {"expiry": "2023-10-26", "price": 2500.0, "oi": 100000},
                "next_month": {"expiry": "2023-11-30", "price": 2515.2, "oi": 190000}
            }
            route.fulfill(json=mock_data)

        page = context.new_page()
        page.route("**/api/market-activity/cash-flow*", mock_cash_flow)
        page.route("**/api/market-activity/participant-oi*", mock_participant_oi)
        page.route("**/api/market-activity/dynamic-chart/*", mock_dynamic_chart)
        page.route("**/api/analysis/oi/*", mock_oi_analysis)
        page.route("**/api/analysis/rollover/*", mock_rollover_analysis)

        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
