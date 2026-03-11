import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Replace the thead for snapshotMode and !snapshotMode to match the 40 columns perfectly.
# Also replace generateTableHTML entirely.

old_generate_start = content.find("const generateTableHTML = (row, isSnapshot) => {")
old_generate_end = content.find("if (snapshotMode) {")

if old_generate_start == -1 or old_generate_end == -1:
    print("Could not find generateTableHTML boundaries")
    exit(1)

new_generate_html = """const generateTableHTML = (row, isSnapshot) => {
                            const close = (row.close_price != null && typeof row.close_price === 'number') ? row.close_price.toFixed(2) : '-';
                            const vwap = (row.vwap != null && typeof row.vwap === 'number') ? row.vwap.toFixed(2) : '-';
                            const fVol = (row.futures_total_vol != null && typeof row.futures_total_vol === 'number') ? row.futures_total_vol.toLocaleString() : '-';
                            const fOi = (row.futures_total_oi != null && typeof row.futures_total_oi === 'number') ? row.futures_total_oi.toLocaleString() : '-';
                            const pcr = (row.pcr_oi != null && typeof row.pcr_oi === 'number') ? row.pcr_oi.toFixed(2) : '-';

                            const hiOiStrikePe = (row.highest_oi_strike_pe != null && typeof row.highest_oi_strike_pe === 'number') ? row.highest_oi_strike_pe.toLocaleString() : '-';
                            const pctAwayPe = (row.pct_away_highest_pe != null && typeof row.pct_away_highest_pe === 'number') ? (row.pct_away_highest_pe).toFixed(2) + '%' : '-';
                            const hiOiStrikeCe = (row.highest_oi_strike_ce != null && typeof row.highest_oi_strike_ce === 'number') ? row.highest_oi_strike_ce.toLocaleString() : '-';
                            const pctAwayCe = (row.pct_away_highest_ce != null && typeof row.pct_away_highest_ce === 'number') ? (row.pct_away_highest_ce).toFixed(2) + '%' : '-';
                            const chgOiOpt = (row.chg_oi_options != null && typeof row.chg_oi_options === 'number') ? row.chg_oi_options.toLocaleString() : '-';
                            const chgOiFut = (row.chg_oi_futures != null && typeof row.chg_oi_futures === 'number') ? row.chg_oi_futures.toLocaleString() : '-';
                            const fut1Exp = row.near_expiry_date !== null ? row.near_expiry_date : '-';
                            const fut2Exp = row.next_expiry_date !== null ? row.next_expiry_date : '-';
                            const fut3Exp = row.far_expiry_date !== null ? row.far_expiry_date : '-';
                            const totCallOi = (row.total_options_call_oi != null && typeof row.total_options_call_oi === 'number') ? row.total_options_call_oi.toLocaleString() : '-';
                            const totPutOi = (row.total_options_put_oi != null && typeof row.total_options_put_oi === 'number') ? row.total_options_put_oi.toLocaleString() : '-';

                            const atmIvNear = (row.atm_iv_near != null && typeof row.atm_iv_near === 'number') ? (row.atm_iv_near * 100).toFixed(2) + '%' : '-';
                            const atmIvNext = (row.atm_iv_next != null && typeof row.atm_iv_next === 'number') ? (row.atm_iv_next * 100).toFixed(2) + '%' : '-';
                            const ivRank = (row.iv_rank_252 != null && typeof row.iv_rank_252 === 'number') ? row.iv_rank_252.toFixed(2) : '-';
                            const ivPctile = (row.iv_percentile_252 != null && typeof row.iv_percentile_252 === 'number') ? row.iv_percentile_252.toFixed(2) : '-';
                            const skewNear = (row.skew_25d_near != null && typeof row.skew_25d_near === 'number') ? (row.skew_25d_near * 100).toFixed(2) + '%' : '-';
                            const skewFar = (row.skew_25d_far != null && typeof row.skew_25d_far === 'number') ? (row.skew_25d_far * 100).toFixed(2) + '%' : '-';
                            const vol1Sig = (row.daily_volatility != null && typeof row.daily_volatility === 'number') ? (row.daily_volatility * 100).toFixed(2) + '%' : '-';

                            const roll = (row.rollover_pct != null && typeof row.rollover_pct === 'number') ? (row.rollover_pct * 100).toFixed(2) + '%' : '-';

                            let mwpl = '0.00';
                            if (row.mwpl_array && Array.isArray(row.mwpl_array) && row.mwpl_array.length > 0) {
                                const firstKey = Object.keys(row.mwpl_array[0])[0];
                                mwpl = row.mwpl_array[0][firstKey].toFixed(2);
                            }

                            const basis1 = (row.basis_1_bps != null && typeof row.basis_1_bps === 'number') ? row.basis_1_bps.toFixed(0) : '-';
                            const basis2 = (row.basis_2_bps != null && typeof row.basis_2_bps === 'number') ? row.basis_2_bps.toFixed(0) : '-';
                            const cal1 = (row.calendar_spread_1_bps != null && typeof row.calendar_spread_1_bps === 'number') ? row.calendar_spread_1_bps.toFixed(0) : '-';
                            const cal2 = (row.calendar_spread_2_bps != null && typeof row.calendar_spread_2_bps === 'number') ? row.calendar_spread_2_bps.toFixed(0) : '-';

                            const pe = (row.pe_ratio != null && typeof row.pe_ratio === 'number') ? row.pe_ratio.toFixed(2) : '-';
                            const b252 = (row.beta_252 != null && typeof row.beta_252 === 'number') ? row.beta_252.toFixed(2) : '-';
                            const b500 = (row.beta_500 != null && typeof row.beta_500 === 'number') ? row.beta_500.toFixed(2) : '-';
                            const r252 = (row.r_squared_252 != null && typeof row.r_squared_252 === 'number') ? row.r_squared_252.toFixed(2) : '-';
                            const r500 = (row.r_squared_500 != null && typeof row.r_squared_500 === 'number') ? row.r_squared_500.toFixed(2) : '-';
                            const pxPct = (row.price_pct_change != null && typeof row.price_pct_change === 'number') ? (row.price_pct_change).toFixed(2) + '%' : '-';
                            const relVol = (row.relative_volume_20d != null && typeof row.relative_volume_20d === 'number') ? row.relative_volume_20d.toFixed(2) : '-';

                            const atr = (row.atr_14_cash != null && typeof row.atr_14_cash === 'number') ? row.atr_14_cash.toFixed(2) : '-';
                            const ema20 = (row.ema_20_cash != null && typeof row.ema_20_cash === 'number') ? row.ema_20_cash.toFixed(2) : '-';
                            const ema50 = (row.ema_50_cash != null && typeof row.ema_50_cash === 'number') ? row.ema_50_cash.toFixed(2) : '-';
                            const ema100 = (row.ema_100_cash != null && typeof row.ema_100_cash === 'number') ? row.ema_100_cash.toFixed(2) : '-';
                            const ema200 = (row.ema_200_cash != null && typeof row.ema_200_cash === 'number') ? row.ema_200_cash.toFixed(2) : '-';

                            // Note: delivery fields don't exist in model, using '-'
                            const del5 = '-';
                            const del10 = '-';
                            const del20 = '-';
                            const del30 = '-';

                            let html = ``;
                            if(!isSnapshot) {
                                html += `<td style="position: sticky; left: 0; background: #1e1e1e; z-index: 2;">${row.trade_date}</td>`;
                                html += `<td style="position: sticky; left: 90px; background: #1e1e1e; z-index: 2;">${row.symbol}</td>`;
                            } else {
                                html += `<td style="position: sticky; left: 0; background: #1e1e1e; z-index: 2;">${row.symbol}</td>`;
                            }

                            html += `
                                <td>${close}</td>
                                <td>${vwap}</td>
                                <td>${fVol}</td>
                                <td>${fOi}</td>
                                <td>${pcr}</td>
                                <td>${hiOiStrikePe}</td>
                                <td>${pctAwayPe}</td>
                                <td>${hiOiStrikeCe}</td>
                                <td>${pctAwayCe}</td>
                                <td>${chgOiOpt}</td>
                                <td>${chgOiFut}</td>
                                <td>${fut1Exp}</td>
                                <td>${fut2Exp}</td>
                                <td>${fut3Exp}</td>
                                <td>${totCallOi}</td>
                                <td>${totPutOi}</td>
                                <td>${atmIvNear}</td>
                                <td>${atmIvNext}</td>
                                <td>${ivRank}</td>
                                <td>${ivPctile}</td>
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
                                <td>${pxPct}</td>
                                <td>${relVol}</td>
                                <td>${atr}</td>
                                <td>${ema20}</td>
                                <td>${ema50}</td>
                                <td>${ema100}</td>
                                <td>${ema200}</td>
                            `;
                            return html;
                        };
                        """

# Find the end of snapshotMode logic
old_headers_end = content.find("statusText.innerText = `Loaded ${data.length} records.`;")

headers_html = """if (snapshotMode) {
                            thead.innerHTML = `
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3;">Symbol</th>
                                    <th style="white-space: pre-wrap;">Close<br>Price</th>
                                    <th style="white-space: pre-wrap;">VWAP</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total Vol</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total OI</th>
                                    <th style="white-space: pre-wrap;">Put-Call<br>Ratio (OI)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (PE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (CE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(CE)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Options)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Futures)</th>
                                    <th style="white-space: pre-wrap;">Fut 1<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 2<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 3<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Call OI</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Put OI</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Next)</th>
                                    <th style="white-space: pre-wrap;">IV Rank<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">IV Percentile<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Far)</th>
                                    <th style="white-space: pre-wrap;">1-Sigma Daily<br>Volatility</th>
                                    <th style="white-space: pre-wrap;">Rollover<br>Percentage</th>
                                    <th style="white-space: pre-wrap;">MWPL %<br>(Top Client)</th>
                                    <th style="white-space: pre-wrap;">Basis 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Basis 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">P/E<br>Ratio</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">Price %<br>Change</th>
                                    <th style="white-space: pre-wrap;">Relative Vol<br>(20d)</th>
                                    <th style="white-space: pre-wrap;">14-Day<br>ATR %</th>
                                    <th style="white-space: pre-wrap;">20-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">50-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">100-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">200-Day<br>EMA</th>
                                </tr>
                            `;
                            data.forEach(row => {
                                const tr = document.createElement('tr');
                                tr.innerHTML = generateTableHTML(row, true);
                                tbody.appendChild(tr);
                            });
                        } else {
                            thead.innerHTML = `
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Date</th>
                                    <th style="text-align: left; position: sticky; top: 0; left: 90px; background: #1e1e1e; z-index: 3;">Symbol</th>
                                    <th style="white-space: pre-wrap;">Close<br>Price</th>
                                    <th style="white-space: pre-wrap;">VWAP</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total Vol</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total OI</th>
                                    <th style="white-space: pre-wrap;">Put-Call<br>Ratio (OI)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (PE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (CE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(CE)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Options)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Futures)</th>
                                    <th style="white-space: pre-wrap;">Fut 1<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 2<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 3<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Call OI</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Put OI</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Next)</th>
                                    <th style="white-space: pre-wrap;">IV Rank<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">IV Percentile<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Far)</th>
                                    <th style="white-space: pre-wrap;">1-Sigma Daily<br>Volatility</th>
                                    <th style="white-space: pre-wrap;">Rollover<br>Percentage</th>
                                    <th style="white-space: pre-wrap;">MWPL %<br>(Top Client)</th>
                                    <th style="white-space: pre-wrap;">Basis 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Basis 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">P/E<br>Ratio</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">Price %<br>Change</th>
                                    <th style="white-space: pre-wrap;">Relative Vol<br>(20d)</th>
                                    <th style="white-space: pre-wrap;">14-Day<br>ATR %</th>
                                    <th style="white-space: pre-wrap;">20-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">50-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">100-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">200-Day<br>EMA</th>
                                </tr>
                            `;
                            data.forEach(row => {
                                const tr = document.createElement('tr');
                                tr.innerHTML = generateTableHTML(row, false);
                                tbody.appendChild(tr);
                            });
                        }
"""

new_content = content[:old_generate_start] + new_generate_html + headers_html + content[old_headers_end:]

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(new_content)
