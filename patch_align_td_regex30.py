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

    # Let me just count it properly:
    # close, eqClose, vwap, eqVol, delPct, fVol, fOi, pcr (8)
    # hiOiStrikePe, pctAwayPe, hiOiPeOi, hiOiPeValue (4)
    # hiOiStrikeCe, pctAwayCe, hiOiCeOi, hiOiCeValue (4)
    # atmStraddleNear, atmStraddleWeekly (2)
    # chgOiOpt, chgOiFut (2)
    # fut1Exp, fut2Exp, fut3Exp (3)
    # totCallOi, totPutOi (2)
    # atmIvNear, atmIvNext, ivRank, ivPctile, skewNear, skewFar, vol1Sig (7)
    # roll, mwpl (2)
    # basis1, basis2, cal1, cal2 (4)
    # pe, b252, b500, r252, r500 (5)
    # pxPct, relVol, atr (3)
    # ema20, ema50, ema100, ema200 (4)
    # Total = 8+4+4+2+2+3+2+7+2+4+5+3+4 = 50 !!!
    print("50 is correct!!")
