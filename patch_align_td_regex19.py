import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    html = f.read()

thead_search = re.search(r'<thead id="mr-data-head">.*?</thead>', html, re.DOTALL)
th_cols = re.findall(r'<th.*?>(.*?)</th>', thead_search.group(0), re.DOTALL)

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

    # Notice that "Highest OI Value (PE)" is missing from my `new_tds` count of 49 in TH!
    # Wait! The TH count is 50. Let me check the actual th columns...
