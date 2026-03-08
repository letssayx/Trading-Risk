import re

with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

# Replace the HTML generator block
html = html.replace("""                        // For the new 29-column schema
                        const generateTableHTML = (row, isSnapshot) => {
                            const fVol = row.futures_total_vol !== null ? row.futures_total_vol.toLocaleString() : '-';
                            const fOi = row.futures_total_oi !== null ? row.futures_total_oi.toLocaleString() : '-';
                            const close = row.close_price !== null ? row.close_price.toFixed(2) : '-';
                            const pcr = row.pcr_oi !== null ? row.pcr_oi.toFixed(2) : '-';
                            const basis = row.basis_1_bps !== null ? row.basis_1_bps.toFixed(0) : '-';

                            // Check array safely
                            let mwpl = '0.00';
                            if (row.mwpl_array && Array.isArray(row.mwpl_array) && row.mwpl_array.length > 0) {
                                // Just grab the top client as an example for the summary grid, or sum it if they want
                                const firstKey = Object.keys(row.mwpl_array[0])[0];
                                mwpl = row.mwpl_array[0][firstKey].toFixed(2);
                            }

                            const atmIv = row.atm_iv_near !== null ? (row.atm_iv_near * 100).toFixed(2) + '%' : '-';
                            const skewNear = row.skew_25d_near !== null ? (row.skew_25d_near * 100).toFixed(2) + '%' : '-';
                            const skewFar = row.skew_25d_far !== null ? (row.skew_25d_far * 100).toFixed(2) + '%' : '-';
                            const roll = row.rollover_pct !== null ? row.rollover_pct.toFixed(2) + '%' : '-';
                            const vol1Sig = row.daily_volatility !== null ? (row.daily_volatility * 100).toFixed(2) + '%' : '-';
                            const atr = row.atr_14_cash !== null ? row.atr_14_cash.toFixed(2) : '-';
                            const beta = row.beta_252 !== null ? row.beta_252.toFixed(2) : '-';

                            let html = isSnapshot ? `<td style="text-align: left;"><strong>${row.symbol}</strong></td>` : `<td style="text-align: left;">${row.trade_date}</td><td><strong>${row.symbol}</strong></td>`;

                            html += `
                                <td>${close}</td>
                                <td>${fVol}</td>
                                <td>${fOi}</td>
                                <td>${pcr}</td>
                                <td>${basis}</td>
                                <td style="color: ${parseFloat(mwpl) > 20 ? '#ff4d4d' : 'inherit'};">${mwpl}% (Top Cli)</td>
                                <td>${atmIv}</td>
                                <td>${skewNear}</td>
                                <td>${skewFar}</td>
                                <td>${roll}</td>
                                <td>${vol1Sig}</td>
                                <td>${atr}</td>
                                <td>${beta}</td>
                            `;
                            return html;
                        };""", """                        // For the new 29-column schema
                        const generateTableHTML = (row, isSnapshot) => {
                            const close = row.close_price !== null ? row.close_price.toFixed(2) : '-';
                            const fVol = row.futures_total_vol !== null ? row.futures_total_vol.toLocaleString() : '-';
                            const fOi = row.futures_total_oi !== null ? row.futures_total_oi.toLocaleString() : '-';
                            const pcr = row.pcr_oi !== null ? row.pcr_oi.toFixed(2) : '-';

                            const atmIvNear = row.atm_iv_near !== null ? (row.atm_iv_near * 100).toFixed(2) + '%' : '-';
                            const atmIvNext = row.atm_iv_next !== null ? (row.atm_iv_next * 100).toFixed(2) + '%' : '-';
                            const skewNear = row.skew_25d_near !== null ? (row.skew_25d_near * 100).toFixed(2) + '%' : '-';
                            const skewFar = row.skew_25d_far !== null ? (row.skew_25d_far * 100).toFixed(2) + '%' : '-';
                            const vol1Sig = row.daily_volatility !== null ? (row.daily_volatility * 100).toFixed(2) + '%' : '-';

                            const roll = row.rollover_pct !== null ? row.rollover_pct.toFixed(2) + '%' : '-';

                            // Check array safely
                            let mwpl = '0.00';
                            if (row.mwpl_array && Array.isArray(row.mwpl_array) && row.mwpl_array.length > 0) {
                                const firstKey = Object.keys(row.mwpl_array[0])[0];
                                mwpl = row.mwpl_array[0][firstKey].toFixed(2);
                            }

                            const basis1 = row.basis_1_bps !== null ? row.basis_1_bps.toFixed(0) : '-';
                            const basis2 = row.basis_2_bps !== null ? row.basis_2_bps.toFixed(0) : '-';
                            const cal1 = row.calendar_spread_1_bps !== null ? row.calendar_spread_1_bps.toFixed(0) : '-';
                            const cal2 = row.calendar_spread_2_bps !== null ? row.calendar_spread_2_bps.toFixed(0) : '-';

                            const pe = row.pe_ratio !== null ? row.pe_ratio.toFixed(2) : '-';
                            const b252 = row.beta_252 !== null ? row.beta_252.toFixed(2) : '-';
                            const b500 = row.beta_500 !== null ? row.beta_500.toFixed(2) : '-';
                            const r252 = row.r_squared_252 !== null ? row.r_squared_252.toFixed(2) : '-';
                            const r500 = row.r_squared_500 !== null ? row.r_squared_500.toFixed(2) : '-';

                            const atr = row.atr_14_cash !== null ? row.atr_14_cash.toFixed(2) : '-';
                            const ema20 = row.ema_20_cash !== null ? row.ema_20_cash.toFixed(2) : '-';
                            const ema50 = row.ema_50_cash !== null ? row.ema_50_cash.toFixed(2) : '-';
                            const ema100 = row.ema_100_cash !== null ? row.ema_100_cash.toFixed(2) : '-';
                            const ema200 = row.ema_200_cash !== null ? row.ema_200_cash.toFixed(2) : '-';

                            const del5 = row.mavg_delivery_vol_pct_5d !== null ? row.mavg_delivery_vol_pct_5d.toFixed(2) + '%' : '-';
                            const del10 = row.mavg_delivery_vol_pct_10d !== null ? row.mavg_delivery_vol_pct_10d.toFixed(2) + '%' : '-';
                            const del20 = row.mavg_delivery_vol_pct_20d !== null ? row.mavg_delivery_vol_pct_20d.toFixed(2) + '%' : '-';
                            const del30 = row.mavg_delivery_vol_pct_30d !== null ? row.mavg_delivery_vol_pct_30d.toFixed(2) + '%' : '-';

                            let html = isSnapshot ? `<td style="text-align: left; position: sticky; left: 0; background: #1e1e1e; z-index: 2;"><strong>${row.symbol}</strong></td>` : `<td style="text-align: left; position: sticky; left: 0; background: #1e1e1e; z-index: 2;">${row.trade_date}</td><td style="position: sticky; left: 80px; background: #1e1e1e; z-index: 2;"><strong>${row.symbol}</strong></td>`;

                            html += `
                                <td>${close}</td>
                                <td>${fVol}</td>
                                <td>${fOi}</td>
                                <td>${pcr}</td>
                                <td>${atmIvNear}</td>
                                <td>${atmIvNext}</td>
                                <td>${skewNear}</td>
                                <td>${skewFar}</td>
                                <td>${vol1Sig}</td>
                                <td>${roll}</td>
                                <td style="color: ${parseFloat(mwpl) > 20 ? '#ff4d4d' : 'inherit'};">${mwpl}% (Top Cli)</td>
                                <td>${basis1}</td>
                                <td>${basis2}</td>
                                <td>${cal1}</td>
                                <td>${cal2}</td>
                                <td>${pe}</td>
                                <td>${b252}</td>
                                <td>${b500}</td>
                                <td>${r252}</td>
                                <td>${r500}</td>
                                <td>${atr}</td>
                                <td>${ema20}</td>
                                <td>${ema50}</td>
                                <td>${ema100}</td>
                                <td>${ema200}</td>
                                <td>${del5}</td>
                                <td>${del10}</td>
                                <td>${del20}</td>
                                <td>${del30}</td>
                            `;
                            return html;
                        };""")

# replace table headers
html = html.replace("""                            <thead id="mr-data-head">
                                <tr>
                                    <th style="text-align: left;">Date</th>
                                    <th>Symbol</th>
                                    <th>Close</th>
                                    <th>Total Vol</th>
                                    <th>Total OI</th>
                                    <th>PCR (OI)</th>
                                    <th>Basis 1 (bps)</th>
                                    <th>MWPL (Top)</th>
                                    <th>ATM IV</th>
                                    <th>Skew (Near)</th>
                                    <th>Skew (Far)</th>
                                    <th>Roll %</th>
                                    <th>1-Sig Vol</th>
                                    <th>ATR(14)</th>
                                    <th>Beta(252)</th>
                                </tr>
                            </thead>
                            <tbody id="mr-data-body">
                                <tr><td colspan="15" style="text-align: center; color: #666; padding: 20px;">Enter a symbol, then click 'Load Timeseries' to view historical data.</td></tr>
                            </tbody>""", """                            <thead id="mr-data-head">
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3;">Date</th>
                                    <th style="position: sticky; top: 0; left: 80px; background: #1e1e1e; z-index: 3;">Symbol</th>
                                    <th>Close</th>
                                    <th>Total Vol</th>
                                    <th>Total OI</th>
                                    <th>PCR (OI)</th>
                                    <th>IV Near</th>
                                    <th>IV Next</th>
                                    <th>Skew Near</th>
                                    <th>Skew Far</th>
                                    <th>1-Sig Vol</th>
                                    <th>Roll %</th>
                                    <th>MWPL Top</th>
                                    <th>Bas 1 (bps)</th>
                                    <th>Bas 2 (bps)</th>
                                    <th>Cal 1 (bps)</th>
                                    <th>Cal 2 (bps)</th>
                                    <th>P/E</th>
                                    <th>B-252</th>
                                    <th>B-500</th>
                                    <th>R2-252</th>
                                    <th>R2-500</th>
                                    <th>ATR(14)</th>
                                    <th>EMA-20</th>
                                    <th>EMA-50</th>
                                    <th>EMA-100</th>
                                    <th>EMA-200</th>
                                    <th>Del-5d</th>
                                    <th>Del-10d</th>
                                    <th>Del-20d</th>
                                    <th>Del-30d</th>
                                </tr>
                            </thead>
                            <tbody id="mr-data-body">
                                <tr><td colspan="31" style="text-align: center; color: #666; padding: 20px;">Enter a symbol, then click 'Load Timeseries' to view historical data.</td></tr>
                            </tbody>""")

html = html.replace("""                            thead.innerHTML = `
                                <tr>
                                    <th style="text-align: left;">Symbol</th>
                                    <th>Close</th>
                                    <th>Total Vol</th>
                                    <th>Total OI</th>
                                    <th>PCR (OI)</th>
                                    <th>Basis 1 (bps)</th>
                                    <th>MWPL (Top)</th>
                                    <th>ATM IV</th>
                                    <th>Skew (Near)</th>
                                    <th>Skew (Far)</th>
                                    <th>Roll %</th>
                                    <th>1-Sig Vol</th>
                                    <th>ATR(14)</th>
                                    <th>Beta(252)</th>
                                </tr>
                            `;""", """                            thead.innerHTML = `
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3;">Symbol</th>
                                    <th>Close</th>
                                    <th>Total Vol</th>
                                    <th>Total OI</th>
                                    <th>PCR (OI)</th>
                                    <th>IV Near</th>
                                    <th>IV Next</th>
                                    <th>Skew Near</th>
                                    <th>Skew Far</th>
                                    <th>1-Sig Vol</th>
                                    <th>Roll %</th>
                                    <th>MWPL Top</th>
                                    <th>Bas 1 (bps)</th>
                                    <th>Bas 2 (bps)</th>
                                    <th>Cal 1 (bps)</th>
                                    <th>Cal 2 (bps)</th>
                                    <th>P/E</th>
                                    <th>B-252</th>
                                    <th>B-500</th>
                                    <th>R2-252</th>
                                    <th>R2-500</th>
                                    <th>ATR(14)</th>
                                    <th>EMA-20</th>
                                    <th>EMA-50</th>
                                    <th>EMA-100</th>
                                    <th>EMA-200</th>
                                    <th>Del-5d</th>
                                    <th>Del-10d</th>
                                    <th>Del-20d</th>
                                    <th>Del-30d</th>
                                </tr>
                            `;""")

html = html.replace("""                            thead.innerHTML = `
                                <tr>
                                    <th style="text-align: left;">Date</th>
                                    <th>Symbol</th>
                                    <th>Close</th>
                                    <th>Total Vol</th>
                                    <th>Total OI</th>
                                    <th>PCR (OI)</th>
                                    <th>Basis 1 (bps)</th>
                                    <th>MWPL (Top)</th>
                                    <th>ATM IV</th>
                                    <th>Skew (Near)</th>
                                    <th>Skew (Far)</th>
                                    <th>Roll %</th>
                                    <th>1-Sig Vol</th>
                                    <th>ATR(14)</th>
                                    <th>Beta(252)</th>
                                </tr>
                            `;""", """                            thead.innerHTML = `
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3;">Date</th>
                                    <th style="position: sticky; top: 0; left: 80px; background: #1e1e1e; z-index: 3;">Symbol</th>
                                    <th>Close</th>
                                    <th>Total Vol</th>
                                    <th>Total OI</th>
                                    <th>PCR (OI)</th>
                                    <th>IV Near</th>
                                    <th>IV Next</th>
                                    <th>Skew Near</th>
                                    <th>Skew Far</th>
                                    <th>1-Sig Vol</th>
                                    <th>Roll %</th>
                                    <th>MWPL Top</th>
                                    <th>Bas 1 (bps)</th>
                                    <th>Bas 2 (bps)</th>
                                    <th>Cal 1 (bps)</th>
                                    <th>Cal 2 (bps)</th>
                                    <th>P/E</th>
                                    <th>B-252</th>
                                    <th>B-500</th>
                                    <th>R2-252</th>
                                    <th>R2-500</th>
                                    <th>ATR(14)</th>
                                    <th>EMA-20</th>
                                    <th>EMA-50</th>
                                    <th>EMA-100</th>
                                    <th>EMA-200</th>
                                    <th>Del-5d</th>
                                    <th>Del-10d</th>
                                    <th>Del-20d</th>
                                    <th>Del-30d</th>
                                </tr>
                            `;""")

# Replace the data-table CSS wrapper to make it scrollable horizontally
html = html.replace("""                    <div style="flex: 1; padding: 20px; overflow-y: auto;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span style="color: #a0a0a0; font-size: 13px;">Symbol Timeseries:</span>
                                <input type="text" id="mr-timeseries-symbol" placeholder="NIFTY" class="turtle-input" style="width: 150px; padding: 5px;">
                                <button class="turtle-btn" onclick="loadTimeseriesData()">Load Timeseries</button>
                            </div>
                        </div>
                        <table class="data-table" id="mr-data-table">""", """                    <div style="flex: 1; padding: 20px; overflow: hidden; display: flex; flex-direction: column;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-shrink: 0;">
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span style="color: #a0a0a0; font-size: 13px;">Symbol Timeseries:</span>
                                <input type="text" id="mr-timeseries-symbol" placeholder="NIFTY" class="turtle-input" style="width: 150px; padding: 5px;">
                                <button class="turtle-btn" onclick="loadTimeseriesData()">Load Timeseries</button>
                            </div>
                        </div>
                        <div style="overflow: auto; flex: 1;">
                            <table class="data-table" id="mr-data-table" style="white-space: nowrap;">""")

html = html.replace("""                            </tbody>
                        </table>
                    </div>""", """                            </tbody>
                            </table>
                        </div>
                    </div>""")

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(html)
