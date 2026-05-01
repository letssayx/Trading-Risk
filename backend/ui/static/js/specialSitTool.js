// Javascript for Special Situation Arb
function switchSpecialSitTab(tabName) {
    document.querySelectorAll('.ss-sub-tab').forEach(el => {
        el.style.display = 'none';
        el.classList.remove('active');
    });

    document.querySelectorAll('#tab-special_arb .wb-tab').forEach(el => {
        el.classList.remove('active');
    });

    const target = document.getElementById(`ss-tab-${tabName}`);
    const btn = document.getElementById(`ss-tab-btn-${tabName}`);

    if (target && btn) {
        target.style.display = 'flex';
        target.classList.add('active');
        btn.classList.add('active');
    }
}


function calculateBuyback(fromPct = false) {
    const totalOutEl = document.getElementById('bb-total-out');
    // If we only have percentages (e.g. from sync), we need a baseline Total Outstanding to convert to shares.
    // Sync will provide totalOutstanding in memory or via an attribute, or we assume a base if total is set.
    let currentTotal = parseFloat(totalOutEl.innerText.replace(/,/g, '')) || 0;

    // We get values depending on where the input came from to keep them synced
    if (fromPct && currentTotal > 0) {
        document.getElementById('bb-promoter').value = Math.round(currentTotal * (parseFloat(document.getElementById('bb-promoter-pct').value) || 0) / 100);
        document.getElementById('bb-fii').value = Math.round(currentTotal * (parseFloat(document.getElementById('bb-fii-pct').value) || 0) / 100);
        document.getElementById('bb-dii').value = Math.round(currentTotal * (parseFloat(document.getElementById('bb-dii-pct').value) || 0) / 100);
        document.getElementById('bb-retail').value = Math.round(currentTotal * (parseFloat(document.getElementById('bb-retail-pct-input').value) || 0) / 100);
        document.getElementById('bb-public').value = Math.round(currentTotal * (parseFloat(document.getElementById('bb-public-pct').value) || 0) / 100);
    }

    const promoter = parseFloat(document.getElementById('bb-promoter').value) || 0;
    const fii = parseFloat(document.getElementById('bb-fii').value) || 0;
    const dii = parseFloat(document.getElementById('bb-dii').value) || 0;
    const retail = parseFloat(document.getElementById('bb-retail').value) || 0;
    const publicVal = parseFloat(document.getElementById('bb-public').value) || 0;

    const totalOut = promoter + fii + dii + retail + publicVal;

    // Update percentages if input came from shares
    if (!fromPct && totalOut > 0) {
        document.getElementById('bb-promoter-pct').value = ((promoter / totalOut) * 100).toFixed(2);
        document.getElementById('bb-fii-pct').value = ((fii / totalOut) * 100).toFixed(2);
        document.getElementById('bb-dii-pct').value = ((dii / totalOut) * 100).toFixed(2);
        document.getElementById('bb-retail-pct-input').value = ((retail / totalOut) * 100).toFixed(2);
        document.getElementById('bb-public-pct').value = ((publicVal / totalOut) * 100).toFixed(2);
    }

    totalOutEl.innerText = totalOut.toLocaleString();

    const totalOffer = parseFloat(document.getElementById('bb-total-offer').value) || 0;
    const retailPct = parseFloat(document.getElementById('bb-retail-pct').value) || 15;

    const resRetailOffer = totalOffer * (retailPct / 100);
    const pubOffer = totalOffer - resRetailOffer;

    document.getElementById('bb-res-retail-offer').innerText = resRetailOffer.toLocaleString() + ' (' + retailPct + '%)';
    document.getElementById('bb-pub-offer').innerText = pubOffer.toLocaleString() + ' (' + (100 - retailPct) + '%)';

    // Price Info
    const buybackPrice = parseFloat(document.getElementById('bb-price').value) || 0;
    const cmp = parseFloat(document.getElementById('bb-cmp').value) || 0;
    const futPrice = parseFloat(document.getElementById('bb-fut-price').value) || 0;
    const sharesCalc = parseFloat(document.getElementById('bb-shares-calc').value) || 100;

    // Promoter Post Event Math
    const participates = document.getElementById('bb-promoter-participates').checked;

    let postPromoterPct = 0;
    if (totalOut > 0) {
        const promoterOwnershipPct = promoter / totalOut;
        let finalPromoterShares = promoter;

        if (participates) {
            finalPromoterShares = promoter - (totalOffer * promoterOwnershipPct);
        }

        const finalTotalShares = totalOut - totalOffer;
        if (finalTotalShares > 0) {
            postPromoterPct = (finalPromoterShares / finalTotalShares) * 100;
        }
    }
    document.getElementById('bb-promoter-post-pct').innerText = postPromoterPct.toFixed(2) + '%';

    // Participation Table logic
    let eligibleNonRetail = totalOut - retail;
    if (!participates) {
        eligibleNonRetail -= promoter;
    }

    const accNon100 = eligibleNonRetail > 0 ? (pubOffer / eligibleNonRetail) : 0;
    const accRet100 = retail > 0 ? (resRetailOffer / retail) : 0;

    // Arbitrage Scenario is for Institutional/Non-Retail
    const baseAccRatio = accNon100 > 1 ? 1 : accNon100;

    const acceptedShares = sharesCalc * baseAccRatio;
    const unacceptedShares = sharesCalc - acceptedShares;

    // 1. Profit from accepted shares
    const eqProfit = (buybackPrice - cmp) * sharesCalc * baseAccRatio;

    // 2. Future P&L
    // The user sells futures to hedge the unaccepted shares.
    // Loss per unaccepted share = (CMP - Fut Price)
    // Positive means a loss, negative means a profit.
    const futLoss = unacceptedShares * (cmp - futPrice);

    // Net Profit = Equity Profit - Future Loss
    const netProfit = eqProfit - futLoss;

    let netPct = 0;
    if (cmp > 0) {
        netPct = (netProfit / (cmp * sharesCalc)) * 100;
    }

    document.getElementById('bb-eq-profit').innerText = eqProfit.toFixed(2);
    // Display futLoss directly (which represents the loss amount)
    document.getElementById('bb-fut-profit').innerText = futLoss.toFixed(2);

    const netProfitEl = document.getElementById('bb-net-profit');
    netProfitEl.innerText = netProfit.toFixed(2);
    netProfitEl.style.color = netProfit >= 0 ? '#10b981' : '#f44336';

    const netPctEl = document.getElementById('bb-net-pct');
    netPctEl.innerText = netPct.toFixed(2) + '%';
    netPctEl.style.color = netProfit >= 0 ? '#10b981' : '#f44336';

    // Populate Participation Table
    const accNon90 = accNon100 / 0.9 > 1 ? 1 : accNon100 / 0.9;
    const accNon80 = accNon100 / 0.8 > 1 ? 1 : accNon100 / 0.8;

    document.getElementById('bb-acc-non-100').innerText = (accNon100 * 100).toFixed(2) + '%';
    document.getElementById('bb-acc-non-90').innerText = (accNon90 * 100).toFixed(2) + '%';
    document.getElementById('bb-acc-non-80').innerText = (accNon80 * 100).toFixed(2) + '%';

    const profNon100 = (buybackPrice - cmp) * accNon100 - (1 - accNon100) * (cmp - futPrice);
    const profNon90 = (buybackPrice - cmp) * accNon90 - (1 - accNon90) * (cmp - futPrice);
    const profNon80 = (buybackPrice - cmp) * accNon80 - (1 - accNon80) * (cmp - futPrice);

    document.getElementById('bb-prof-non-100').innerText = '₹' + profNon100.toFixed(2);
    document.getElementById('bb-prof-non-90').innerText = '₹' + profNon90.toFixed(2);
    document.getElementById('bb-prof-non-80').innerText = '₹' + profNon80.toFixed(2);

    const accRet90 = accRet100 / 0.9 > 1 ? 1 : accRet100 / 0.9;
    const accRet80 = accRet100 / 0.8 > 1 ? 1 : accRet100 / 0.8;

    document.getElementById('bb-acc-ret-100').innerText = (accRet100 * 100).toFixed(2) + '%';
    document.getElementById('bb-acc-ret-90').innerText = (accRet90 * 100).toFixed(2) + '%';
    document.getElementById('bb-acc-ret-80').innerText = (accRet80 * 100).toFixed(2) + '%';

    const profRet100 = (buybackPrice - cmp) * accRet100 - (1 - accRet100) * (cmp - futPrice);
    const profRet90 = (buybackPrice - cmp) * accRet90 - (1 - accRet90) * (cmp - futPrice);
    const profRet80 = (buybackPrice - cmp) * accRet80 - (1 - accRet80) * (cmp - futPrice);

    document.getElementById('bb-prof-ret-100').innerText = '₹' + profRet100.toFixed(2);
    document.getElementById('bb-prof-ret-90').innerText = '₹' + profRet90.toFixed(2);
    document.getElementById('bb-prof-ret-80').innerText = '₹' + profRet80.toFixed(2);
}








async function syncBuybackHoldings(event) {
    let btn = event ? event.currentTarget : null;
    let originalHtml = '';
    if (btn) {
        originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
        btn.disabled = true;
    }
    const symbol = document.getElementById('bb-symbol').value.toUpperCase();
    if (!symbol) {
        alert("Please enter a symbol in Price Info to sync holdings.");
        return;
    }

    try {
        const res = await fetch(`/api/data/shareholding?symbol=${symbol}`);
        if (!res.ok) throw new Error("Network response was not ok");
        const data = await res.json();

        if (data && data.total_outstanding) {
            document.getElementById('bb-total-out').innerText = data.total_outstanding;

            document.getElementById('bb-promoter-pct').value = data.promoter_holding || 0;
            document.getElementById('bb-fii-pct').value = data.fii_holding || 0;
            document.getElementById('bb-dii-pct').value = data.dii_holding || 0;
            document.getElementById('bb-retail-pct-input').value = data.retail_holding || 0;
            document.getElementById('bb-public-pct').value = data.public_holding || 0;

            // If absolute values were provided by the API (e.g. from exact NSE XBRL parser)
            if (data.promoter_shares !== undefined) {
                document.getElementById('bb-promoter').value = data.promoter_shares || 0;
                document.getElementById('bb-fii').value = data.fii_shares || 0;
                document.getElementById('bb-dii').value = data.dii_shares || 0;
                document.getElementById('bb-retail').value = data.retail_shares || 0;
                document.getElementById('bb-public').value = data.public_shares || 0;
                calculateBuyback(false); // Math using exact absolute shares
            } else {
                calculateBuyback(true); // Math falls back to percentage conversion
            }
        } else {
             alert("No shareholding data returned.");
        }
    } catch (e) {
        console.error("Error syncing fundamentals", e);
        alert("Failed to sync holdings from Backend. Check console.");
    } finally {
        if (btn) {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
    }
}

// Store fetched futures prices globally so they can be swapped dynamically when selection changes
let fetchedFutures = {
    '1': 0,
    '2': 0,
    '3': 0
};

let fetchedOFSFutures = {
    '1': 0,
    '2': 0,
    '3': 0
};

function handleFutureSelectionChange() {
    const sel = document.getElementById('bb-future-sel').value;
    if (fetchedFutures[sel]) {
        document.getElementById('bb-fut-price').value = parseFloat(fetchedFutures[sel]).toFixed(2);
    }
    calculateBuyback();
}

function handleOFSFutureSelectionChange() {
    const sel = document.getElementById('ofs-future-sel').value;
    if (fetchedOFSFutures[sel]) {
        document.getElementById('ofs-fut-price').value = parseFloat(fetchedOFSFutures[sel]).toFixed(2);
        document.getElementById('ofs-hedge-entry').value = parseFloat(fetchedOFSFutures[sel]).toFixed(2);
    }
    calculateOFS();
}

async function syncBuybackPrices(event) {
    let btn = event ? event.currentTarget : null;
    let originalHtml = '';
    if (btn) {
        originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
        btn.disabled = true;
    }
    const symbol = document.getElementById('bb-symbol').value.toUpperCase();
    if (!symbol) return;

    try {
        const res = await fetch(`/api/data/live_price?symbol=${symbol}`);
        if (!res.ok) throw new Error("Network response was not ok");
        const data = await res.json();

        if (data && data.price) {
            document.getElementById('bb-cmp').value = parseFloat(data.price).toFixed(2) || 0;

            // Store prices
            fetchedFutures['1'] = data.near_fut_price || 0;
            fetchedFutures['2'] = data.next_fut_price || 0;
            fetchedFutures['3'] = data.far_fut_price || 0;

            const sel = document.getElementById('bb-future-sel').value;
            if (fetchedFutures[sel]) {
                document.getElementById('bb-fut-price').value = parseFloat(fetchedFutures[sel]).toFixed(2);
            }
            calculateBuyback();
        } else {
             alert("No price data returned.");
        }
    } catch (e) {
        console.error("Error fetching price", e);
    } finally {
        if (btn) {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
    }
}

window.switchSpecialSitTab = switchSpecialSitTab;
window.calculateBuyback = calculateBuyback;
window.syncBuybackHoldings = syncBuybackHoldings;
window.syncBuybackPrices = syncBuybackPrices;

function calculateOFS(fromPct = false) {
    const totalOutEl = document.getElementById('ofs-total-out');
    let currentTotal = parseFloat(totalOutEl.innerText.replace(/,/g, '')) || 0;

    if (fromPct && currentTotal > 0) {
        document.getElementById('ofs-promoter').value = Math.round(currentTotal * (parseFloat(document.getElementById('ofs-promoter-pct').value) || 0) / 100);
        document.getElementById('ofs-fii').value = Math.round(currentTotal * (parseFloat(document.getElementById('ofs-fii-pct').value) || 0) / 100);
        document.getElementById('ofs-dii').value = Math.round(currentTotal * (parseFloat(document.getElementById('ofs-dii-pct').value) || 0) / 100);
        document.getElementById('ofs-retail').value = Math.round(currentTotal * (parseFloat(document.getElementById('ofs-retail-pct-input').value) || 0) / 100);
    }

    const promoter = parseFloat(document.getElementById('ofs-promoter').value) || 0;
    const fii = parseFloat(document.getElementById('ofs-fii').value) || 0;
    const dii = parseFloat(document.getElementById('ofs-dii').value) || 0;
    const retail = parseFloat(document.getElementById('ofs-retail').value) || 0;

    const totalOut = promoter + fii + dii + retail;

    if (!fromPct && totalOut > 0) {
        document.getElementById('ofs-promoter-pct').value = ((promoter / totalOut) * 100).toFixed(2);
        document.getElementById('ofs-fii-pct').value = ((fii / totalOut) * 100).toFixed(2);
        document.getElementById('ofs-dii-pct').value = ((dii / totalOut) * 100).toFixed(2);
        document.getElementById('ofs-retail-pct-input').value = ((retail / totalOut) * 100).toFixed(2);
    }

    totalOutEl.innerText = totalOut.toLocaleString();

    const totalOffer = parseFloat(document.getElementById('ofs-total-offer').value) || 0;
    const retailPct = parseFloat(document.getElementById('ofs-retail-pct').value) || 10;

    // Total available for our category (assuming non-retail for now, or just generic OFS math)
    const availableSupply = totalOffer;

    const cmp = parseFloat(document.getElementById('ofs-cmp').value) || 0;
    const bidPrice = parseFloat(document.getElementById('ofs-bid-price').value) || 0;
    const hedgeEntry = parseFloat(document.getElementById('ofs-hedge-entry').value) || 0;
    const lotSize = parseFloat(document.getElementById('ofs-lot-size').value) || 0;
    const lots = parseFloat(document.getElementById('ofs-lots').value) || 0;

    const cof = parseFloat(document.getElementById('ofs-cof').value) || 0;
    const impact = parseFloat(document.getElementById('ofs-impact').value) || 0;
    const stt = parseFloat(document.getElementById('ofs-stt').value) || 0;

    const totalSharesBid = lotSize * lots;

    // Gross Spread
    const grossSpread = cmp - bidPrice;
    document.getElementById('ofs-gross-spread').innerText = grossSpread.toFixed(2);

    // Arbitrage %
    let arbPct = 0;
    if (cmp > 0) {
        arbPct = (grossSpread / cmp) * 100;
    }
    document.getElementById('ofs-arb-pct').innerText = arbPct.toFixed(2) + '%';

    // Waterfall Allocation Matrix
    let bid1 = bidPrice;
    let bid2 = bidPrice - 1;
    let bid3 = bidPrice - 2;

    let qty1 = lotSize * lots;
    let qty2 = lotSize * lots;
    let qty3 = lotSize * lots;

    let cum1 = 12000000;
    let cum2 = 5000000;
    let cum3 = 1000000;

    const tbody = document.getElementById('ofs-matrix-body');
    if (tbody && tbody.children.length > 0) {
        try {
            bid1 = parseFloat(tbody.children[0].querySelectorAll('input')[0].value) || bid1;
            qty1 = parseFloat(tbody.children[0].querySelectorAll('input')[1].value) || qty1;
            cum1 = parseFloat(tbody.children[0].querySelectorAll('input')[2].value) || cum1;

            bid2 = parseFloat(tbody.children[1].querySelectorAll('input')[0].value) || bid2;
            qty2 = parseFloat(tbody.children[1].querySelectorAll('input')[1].value) || qty2;
            cum2 = parseFloat(tbody.children[1].querySelectorAll('input')[2].value) || cum2;

            bid3 = parseFloat(tbody.children[2].querySelectorAll('input')[0].value) || bid3;
            qty3 = parseFloat(tbody.children[2].querySelectorAll('input')[1].value) || qty3;
            cum3 = parseFloat(tbody.children[2].querySelectorAll('input')[2].value) || cum3;
        } catch (e) {}
    }

    let remainingSupply = availableSupply;

    let allot1 = 0;
    if (cum1 > 0) {
        allot1 = (remainingSupply / cum1) * 100;
        if (allot1 > 100) allot1 = 100;
    }
    const allocatedAt1 = cum1 * (allot1 / 100);
    remainingSupply = Math.max(0, remainingSupply - allocatedAt1);
    const shareAllot1 = Math.floor(qty1 * (allot1 / 100));

    let allot2 = 0;
    if (cum2 > 0 && remainingSupply > 0) {
        allot2 = (remainingSupply / cum2) * 100;
        if (allot2 > 100) allot2 = 100;
    }
    const allocatedAt2 = cum2 * (allot2 / 100);
    remainingSupply = Math.max(0, remainingSupply - allocatedAt2);
    const shareAllot2 = Math.floor(qty2 * (allot2 / 100));

    let allot3 = 0;
    if (cum3 > 0 && remainingSupply > 0) {
        allot3 = (remainingSupply / cum3) * 100;
        if (allot3 > 100) allot3 = 100;
    }
    const shareAllot3 = Math.floor(qty3 * (allot3 / 100));

    if (tbody) {
        tbody.innerHTML = `
            <tr style="text-align: right;">
                <td style="text-align: left; padding: 4px; border: 1px solid #444;">
                    <input type="number" class="history-input" style="width: 80px;" value="${bid1.toFixed(2)}" oninput="calculateOFS()">
                </td>
                <td style="padding: 4px; border: 1px solid #444;">
                    <input type="number" class="history-input" style="width: 80px;" value="${qty1}" oninput="calculateOFS()">
                </td>
                <td style="padding: 4px; border: 1px solid #444;">
                    <input type="number" class="history-input" style="width: 100px;" value="${cum1}" oninput="calculateOFS()">
                </td>
                <td style="padding: 4px; border: 1px solid #444; color: ${allot1 > 0 ? '#FFD700' : '#888'}; font-weight: ${allot1 > 0 ? 'bold' : 'normal'};">${allot1.toFixed(2)}%</td>
                <td style="padding: 4px; border: 1px solid #444;">${shareAllot1}</td>
            </tr>
            <tr style="text-align: right;">
                <td style="text-align: left; padding: 4px; border: 1px solid #444;">
                    <input type="number" class="history-input" style="width: 80px;" value="${bid2.toFixed(2)}" oninput="calculateOFS()">
                </td>
                <td style="padding: 4px; border: 1px solid #444;">
                    <input type="number" class="history-input" style="width: 80px;" value="${qty2}" oninput="calculateOFS()">
                </td>
                <td style="padding: 4px; border: 1px solid #444;">
                    <input type="number" class="history-input" style="width: 100px;" value="${cum2}" oninput="calculateOFS()">
                </td>
                <td style="padding: 4px; border: 1px solid #444; color: ${allot2 > 0 ? '#FFD700' : '#888'}; font-weight: ${allot2 > 0 ? 'bold' : 'normal'};">${allot2.toFixed(2)}%</td>
                <td style="padding: 4px; border: 1px solid #444;">${shareAllot2}</td>
            </tr>
            <tr style="text-align: right;">
                <td style="text-align: left; padding: 4px; border: 1px solid #444;">
                    <input type="number" class="history-input" style="width: 80px;" value="${bid3.toFixed(2)}" oninput="calculateOFS()">
                </td>
                <td style="padding: 4px; border: 1px solid #444;">
                    <input type="number" class="history-input" style="width: 80px;" value="${qty3}" oninput="calculateOFS()">
                </td>
                <td style="padding: 4px; border: 1px solid #444;">
                    <input type="number" class="history-input" style="width: 100px;" value="${cum3}" oninput="calculateOFS()">
                </td>
                <td style="padding: 4px; border: 1px solid #444; color: ${allot3 > 0 ? '#FFD700' : '#888'}; font-weight: ${allot3 > 0 ? 'bold' : 'normal'};">${allot3.toFixed(2)}%</td>
                <td style="padding: 4px; border: 1px solid #444;">${shareAllot3}</td>
            </tr>
        `;
    }

    document.getElementById('ofs-shares-allotted').innerText = shareAllot1;

    const unhedged = totalSharesBid - shareAllot1;
    let reversal = 0;
    if (unhedged > 0 && shareAllot1 > 0) {
        reversal = hedgeEntry - (grossSpread * shareAllot1 / unhedged);
    } else {
        reversal = hedgeEntry;
    }
    document.getElementById('ofs-reversal-price').innerText = reversal.toFixed(2);

    const futRisk = (unhedged / (lotSize || 1));
    document.getElementById('ofs-fut-risk').innerText = futRisk.toFixed(2);

    let futRiskPct = 0;
    if (totalSharesBid > 0) {
        futRiskPct = (unhedged / totalSharesBid) * 100;
    }
    document.getElementById('ofs-fut-risk-pct').innerText = futRiskPct.toFixed(2) + '%';

    const totalCosts = cof + impact + stt;
    const netArbPct = arbPct - totalCosts;
    document.getElementById('ofs-net-arb-pct').innerText = netArbPct.toFixed(2) + '%';
}





async function syncOFSHoldings(event) {
    let btn = event ? event.currentTarget : null;
    let originalHtml = '';
    if (btn) {
        originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
        btn.disabled = true;
    }
    const symbol = document.getElementById('ofs-symbol').value.toUpperCase();
    if (!symbol) {
        alert("Please enter a symbol in Price Info to sync holdings.");
        return;
    }

    try {
        const res = await fetch(`/api/data/shareholding?symbol=${symbol}`);
        if (!res.ok) throw new Error("Network response was not ok");
        const data = await res.json();

        if (data && data.total_outstanding) {
            document.getElementById('ofs-total-out').innerText = data.total_outstanding;

            document.getElementById('ofs-promoter-pct').value = data.promoter_holding || 0;
            document.getElementById('ofs-fii-pct').value = data.fii_holding || 0;
            document.getElementById('ofs-dii-pct').value = data.dii_holding || 0;
            document.getElementById('ofs-retail-pct-input').value = data.public_holding || 0;

            if (data.promoter_shares !== undefined) {
                document.getElementById('ofs-promoter').value = data.promoter_shares || 0;
                document.getElementById('ofs-fii').value = data.fii_shares || 0;
                document.getElementById('ofs-dii').value = data.dii_shares || 0;
                // For OFS, retail is currently just capturing the generic public block
                document.getElementById('ofs-retail').value = data.public_shares || 0;
                calculateOFS(false);
            } else {
                calculateOFS(true);
            }
        } else {
            alert("No shareholding data returned.");
        }
    } catch (e) {
        console.error("Error syncing OFS fundamentals", e);
        alert("Failed to sync holdings from Backend. Check console.");
    } finally {
        if (btn) {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
    }
}

async function syncOFSPrices(event) {
    let btn = event ? event.currentTarget : null;
    let originalHtml = '';
    if (btn) {
        originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
        btn.disabled = true;
    }
    const symbol = document.getElementById('ofs-symbol').value.toUpperCase();
    if (!symbol) return;

    try {
        const res = await fetch(`/api/data/live_price?symbol=${symbol}`);
        if (!res.ok) throw new Error("Network response was not ok");
        const data = await res.json();

        if (data && data.price) {
            const price = parseFloat(data.price).toFixed(2);
            document.getElementById('ofs-cmp').value = price || 0;

            // Store OFS prices
            fetchedOFSFutures['1'] = data.near_fut_price || 0;
            fetchedOFSFutures['2'] = data.next_fut_price || 0;
            fetchedOFSFutures['3'] = data.far_fut_price || 0;

            const sel = document.getElementById('ofs-future-sel').value;
            if (fetchedOFSFutures[sel] && parseFloat(fetchedOFSFutures[sel]) > 0) {
                const futPrice = parseFloat(fetchedOFSFutures[sel]).toFixed(2);
                document.getElementById('ofs-fut-price').value = futPrice;
                document.getElementById('ofs-hedge-entry').value = futPrice;
            } else {
                document.getElementById('ofs-hedge-entry').value = price || 0;
                document.getElementById('ofs-fut-price').value = price || 0;
            }

            calculateOFS();
        } else {
             alert("No price data returned.");
        }
    } catch (e) {
        console.error("Error fetching OFS price", e);
    } finally {
        if (btn) {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
    }
}

window.calculateOFS = calculateOFS;
window.syncOFSHoldings = syncOFSHoldings;
window.syncOFSPrices = syncOFSPrices;
window.handleOFSFutureSelectionChange = handleOFSFutureSelectionChange;


function exportBuybackDataToCSV() {
    let csvData = [];
    csvData.push(["Metric", "Value"]);

    // Inputs
    csvData.push(["Symbol", document.getElementById('bb-symbol').value]);
    csvData.push(["CMP", document.getElementById('bb-cmp').value]);
    csvData.push(["Buyback Price", document.getElementById('bb-price').value]);
    csvData.push(["Total Outstanding", document.getElementById('bb-total-out').innerText]);
    csvData.push(["Total Offer", document.getElementById('bb-total-offer').value]);
    csvData.push(["Retail Reserved %", document.getElementById('bb-retail-pct').value]);
    csvData.push(["Shares Calculated", document.getElementById('bb-shares-calc').value]);
    csvData.push(["Promoter Shares", document.getElementById('bb-promoter').value]);
    csvData.push(["FII Shares", document.getElementById('bb-fii').value]);
    csvData.push(["DII Shares", document.getElementById('bb-dii').value]);
    csvData.push(["Retail Shares", document.getElementById('bb-retail').value]);
    csvData.push(["Public Shares", document.getElementById('bb-public').value]);
    csvData.push(["Promoter Participates", document.getElementById('bb-promoter-participates').checked ? "Yes" : "No"]);

    // Future details
    const futureSel = document.getElementById('bb-future-sel');
    csvData.push(["Selected Future", futureSel.options[futureSel.selectedIndex].text]);
    csvData.push(["Future Price", document.getElementById('bb-fut-price').value]);

    // Computed outputs
    csvData.push(["Post Buyback Promoter %", document.getElementById('bb-res-promoter-post').innerText]);
    csvData.push(["Base Acceptance Ratio %", document.getElementById('bb-res-base-acc-ratio').innerText]);

    csvData.push(["", ""]);
    csvData.push(["Scenario", "Acceptance Ratio", "Equity Profit", "Future Profit", "Net Profit"]);

    csvData.push([
        "Non-Retail (Promoter Participates)",
        document.getElementById('bb-acc-non-100').innerText,
        document.getElementById('bb-eq-prof-non-100').innerText,
        document.getElementById('bb-fut-prof-non-100').innerText,
        document.getElementById('bb-net-prof-non-100').innerText
    ]);
    csvData.push([
        "Non-Retail (90% Accept)",
        document.getElementById('bb-acc-non-90').innerText,
        document.getElementById('bb-eq-prof-non-90').innerText,
        document.getElementById('bb-fut-prof-non-90').innerText,
        document.getElementById('bb-net-prof-non-90').innerText
    ]);
    csvData.push([
        "Non-Retail (80% Accept)",
        document.getElementById('bb-acc-non-80').innerText,
        document.getElementById('bb-eq-prof-non-80').innerText,
        document.getElementById('bb-fut-prof-non-80').innerText,
        document.getElementById('bb-net-prof-non-80').innerText
    ]);

    csvData.push([
        "Retail (100% Acceptance)",
        document.getElementById('bb-acc-ret-100').innerText,
        document.getElementById('bb-eq-prof-ret-100').innerText,
        document.getElementById('bb-fut-prof-ret-100').innerText,
        document.getElementById('bb-net-prof-ret-100').innerText
    ]);
    csvData.push([
        "Retail (90% Acceptance)",
        document.getElementById('bb-acc-ret-90').innerText,
        document.getElementById('bb-eq-prof-ret-90').innerText,
        document.getElementById('bb-fut-prof-ret-90').innerText,
        document.getElementById('bb-net-prof-ret-90').innerText
    ]);
    csvData.push([
        "Retail (80% Acceptance)",
        document.getElementById('bb-acc-ret-80').innerText,
        document.getElementById('bb-eq-prof-ret-80').innerText,
        document.getElementById('bb-fut-prof-ret-80').innerText,
        document.getElementById('bb-net-prof-ret-80').innerText
    ]);

    const csvContent = csvData.map(e => e.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "Buyback_Analysis.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function exportOFSDataToCSV() {
    let csvData = [];
    csvData.push(["Metric", "Value"]);

    // Inputs
    csvData.push(["Symbol", document.getElementById('ofs-symbol').value]);
    csvData.push(["CMP", document.getElementById('ofs-cmp').value]);
    csvData.push(["Floor Price", document.getElementById('ofs-floor-price').value]);
    csvData.push(["Bid Price / Cut-off", document.getElementById('ofs-bid-price').value]);
    csvData.push(["Hedge Entry (Short)", document.getElementById('ofs-hedge-entry').value]);
    csvData.push(["Futures Lot size", document.getElementById('ofs-lot-size').value]);
    csvData.push(["No. of lots (Bid)", document.getElementById('ofs-lots').value]);
    csvData.push(["Cost of Funds %", document.getElementById('ofs-cof').value]);
    csvData.push(["Impact Cost %", document.getElementById('ofs-impact').value]);
    csvData.push(["STT+others %", document.getElementById('ofs-stt').value]);

    csvData.push(["Total Outstanding", document.getElementById('ofs-total-out').innerText]);
    csvData.push(["Total OFS Offer", document.getElementById('ofs-total-offer').value]);
    csvData.push(["Reserved Retail %", document.getElementById('ofs-retail-pct').value]);

    // Future details
    const futureSel = document.getElementById('ofs-future-sel');
    csvData.push(["Selected Future", futureSel.options[futureSel.selectedIndex].text]);
    csvData.push(["Future Price", document.getElementById('ofs-fut-price').value]);

    // Computed Net Outcomes
    csvData.push(["Gross Spread", document.getElementById('ofs-gross-spread').innerText]);
    csvData.push(["Arbitrage %", document.getElementById('ofs-arb-pct').innerText]);
    csvData.push(["Shares Allotted", document.getElementById('ofs-shares-allotted').innerText]);
    csvData.push(["Reversal Price", document.getElementById('ofs-reversal-price').innerText]);
    csvData.push(["Futures Risk Amount", document.getElementById('ofs-fut-risk').innerText]);
    csvData.push(["Futures Risk %", document.getElementById('ofs-fut-risk-pct').innerText]);
    csvData.push(["Net Arbitrage %", document.getElementById('ofs-net-arb-pct').innerText]);

    // Matrix
    csvData.push(["", ""]);
    csvData.push(["Price", "Qty Bid", "Cumul. Qty", "Allotment %", "Shares Allotted"]);

    const matrixBody = document.getElementById('ofs-matrix-body');
    const rows = matrixBody.querySelectorAll('tr');
    rows.forEach(row => {
        let rowData = [];
        row.querySelectorAll('td').forEach(cell => rowData.push(cell.innerText));
        csvData.push(rowData);
    });

    const csvContent = csvData.map(e => e.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "OFS_Analysis.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

window.exportBuybackDataToCSV = exportBuybackDataToCSV;
window.exportOFSDataToCSV = exportOFSDataToCSV;
