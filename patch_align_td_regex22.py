import re

with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
    js = f.read()

match = re.search(r'<td>\$\{close\}</td>.*?<td>\$\{ema200\}</td>', js, re.DOTALL)
if match:
    new_tds = """<td>${close}</td>
                                <td>${eqClose}</td>
                                <td>${vwap}</td>
                                <td>${eqVol}</td>
                                <td>${delPct}%</td>
                                <td>${fVol}</td>
                                <td>${fOi}</td>
                                <td>${pcr}</td>
                                <td>${hiOiStrikePe}</td>
                                <td>${pctAwayPe}</td>
                                <td>${hiOiPeValue}</td>
                                <td>${hiOiStrikeCe}</td>
                                <td>${pctAwayCe}</td>
                                <td>${hiOiCeValue}</td>
                                <td>${atmStraddleNear}</td>
                                <td>${atmStraddleWeekly}</td>
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
                                <td style="color: ${parseFloat(mwpl) > 20 ? '#ff4d4d' : 'inherit'};">${mwpl}</td>
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
                                <td>${ema200}</td>"""

    new_tds = """<td>${close}</td>
                                <td>${eqClose}</td>
                                <td>${vwap}</td>
                                <td>${eqVol}</td>
                                <td>${delPct}%</td>
                                <td>${fVol}</td>
                                <td>${fOi}</td>
                                <td>${pcr}</td>
                                <td>${hiOiStrikePe}</td>
                                <td>${pctAwayPe}</td>
                                <td>${hiOiPeOi}</td>
                                <td>${hiOiPeValue}</td>
                                <td>${hiOiStrikeCe}</td>
                                <td>${pctAwayCe}</td>
                                <td>${hiOiCeOi}</td>
                                <td>${hiOiCeValue}</td>
                                <td>${atmStraddleNear}</td>
                                <td>${atmStraddleWeekly}</td>
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
                                <td style="color: ${parseFloat(mwpl) > 20 ? '#ff4d4d' : 'inherit'};">${mwpl}</td>
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
                                <td>${ema200}</td>"""

    js = js[:match.start()] + new_tds + js[match.end():]
    with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
        f.write(js)
    print("Replaced TD using simplified regex!")

with open('backend/ui/templates/workbench.html', 'r') as f:
    html = f.read()

thead_search = re.search(r'<thead id="mr-data-head">.*?</thead>', html, re.DOTALL)
old_th = thead_search.group(0)
new_th = """<thead id="mr-data-head">
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Date</th>
                                    <th style="text-align: left; position: sticky; top: 0; left: 90px; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Symbol</th>
                                    <th style="white-space: pre-wrap;">Near Fut<br>Close</th>
                                    <th style="white-space: pre-wrap;">EQ<br>Close</th>
                                    <th style="white-space: pre-wrap;">VWAP</th>
                                    <th style="white-space: pre-wrap;">Total EQ<br>Volume</th>
                                    <th style="white-space: pre-wrap;">Delivery<br>(%)</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total Vol</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total OI</th>
                                    <th style="white-space: pre-wrap;">Put-Call<br>Ratio (OI)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (PE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>(PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Value (PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (CE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(CE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>(CE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Value (CE)</th>
                                    <th style="white-space: pre-wrap;">ATM Straddle<br>(Near Month)</th>
                                    <th style="white-space: pre-wrap;">ATM Straddle<br>(Weekly NIFTY)</th>
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
                            </thead>"""
html = html.replace(old_th, new_th)
with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(html)
