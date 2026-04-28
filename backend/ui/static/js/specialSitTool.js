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

    // Is the user calculating for retail or non-retail? Based on total value
    const isRetail = (sharesCalc * cmp) <= 200000;
    const baseAccRatio = isRetail ? accRet100 : accNon100;

    const acceptedShares = sharesCalc * baseAccRatio;
    const unacceptedShares = sharesCalc - acceptedShares;

    // 1. Profit from accepted shares
    // (Buyback Price - CMP) * total_shares * acceptance_ratio
    const eqProfit = (buybackPrice - cmp) * sharesCalc * baseAccRatio;


    // 2. Future P&L
    // user said "loss is 3*no of unaccepted shares" for CMP 200, FUT 203. (200 - 203 = -3).
    const futLoss = unacceptedShares * (cmp - futPrice);


    const netProfit = eqProfit + futLoss;

    let netPct = 0;
    if (cmp > 0) {
        netPct = (netProfit / (cmp * sharesCalc)) * 100;
    }

    document.getElementById('bb-eq-profit').innerText = eqProfit.toFixed(2);
    document.getElementById('bb-fut-profit').innerText = futLoss.toFixed(2);

    const netProfitEl = document.getElementById('bb-net-profit');
    netProfitEl.innerText = netProfit.toFixed(2);
    netProfitEl.style.color = netProfit >= 0 ? '#10b981' : '#f44336';

    const netPctEl = document.getElementById('bb-net-pct');
    netPctEl.innerText = netPct.toFixed(2) + '%';
    netPctEl.style.color = netProfit >= 0 ? '#10b981' : '#f44336';

    document.getElementById('bb-acc-non-100').innerText = (accNon100 * 100).toFixed(2) + '%';
    document.getElementById('bb-acc-non-90').innerText = (accNon100 * 100 / 0.9).toFixed(2) + '%';
    document.getElementById('bb-acc-non-80').innerText = (accNon100 * 100 / 0.8).toFixed(2) + '%';

    document.getElementById('bb-acc-ret-100').innerText = (accRet100 * 100).toFixed(2) + '%';
    document.getElementById('bb-acc-ret-90').innerText = (accRet100 * 100 / 0.9).toFixed(2) + '%';
    document.getElementById('bb-acc-ret-80').innerText = (accRet100 * 100 / 0.8).toFixed(2) + '%';
}








async function syncBuybackHoldings() {
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
            document.getElementById('bb-public-pct').value = data.public_holding || 0;

            calculateBuyback(true);
        } else {
             alert("No shareholding data returned.");
        }
    } catch (e) {
        console.error("Error syncing fundamentals", e);
        alert("Failed to sync holdings from Backend. Check console.");
    }
}

async function syncBuybackPrices() {
    const symbol = document.getElementById('bb-symbol').value.toUpperCase();
    if (!symbol) return;

    try {
        const res = await fetch(`/api/morning-report/timeseries?symbol=${symbol}`);
        const data = await res.json();

        if (data.history && data.history.length > 0) {
            const latest = data.history[0];
            document.getElementById('bb-cmp').value = latest.price || 0;
            if (latest.fut_price) {
                document.getElementById('bb-fut-price').value = latest.fut_price;
            }
            calculateBuyback();
        }
    } catch (e) {
        console.error("Error fetching price", e);
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





async function syncOFSHoldings() {
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

            calculateOFS(true);
        } else {
            alert("No shareholding data returned.");
        }
    } catch (e) {
        console.error("Error syncing OFS fundamentals", e);
        alert("Failed to sync holdings from Backend. Check console.");
    }
}

async function syncOFSPrices() {
    const symbol = document.getElementById('ofs-symbol').value.toUpperCase();
    if (!symbol) return;

    try {
        const res = await fetch(`/api/morning-report/timeseries?symbol=${symbol}`);
        const data = await res.json();

        if (data.history && data.history.length > 0) {
            const latest = data.history[0];
            document.getElementById('ofs-cmp').value = latest.price || 0;
            document.getElementById('ofs-hedge-entry').value = latest.price || 0;
            calculateOFS();
        }
    } catch (e) {
        console.error("Error fetching OFS price", e);
    }
}

window.calculateOFS = calculateOFS;
window.syncOFSHoldings = syncOFSHoldings;
window.syncOFSPrices = syncOFSPrices;
