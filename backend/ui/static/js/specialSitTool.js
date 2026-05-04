// Javascript for Special Situation Arb

function toggleBBVerification() {
    const chk = document.getElementById('bb-verify-chk');
    const badge = document.getElementById('bb-verify-badge');
    if (chk.checked) {
        badge.innerText = 'Verified';
        badge.style.color = '#10b981';
        badge.style.borderColor = '#10b981';
    } else {
        badge.innerText = 'Unverified';
        badge.style.color = '#ff4d4d';
        badge.style.borderColor = '#ff4d4d';
    }
}

function toggleOFSVerification() {
    const chk = document.getElementById('ofs-verify-chk');
    const badge = document.getElementById('ofs-verify-badge');
    if (chk.checked) {
        badge.innerText = 'Verified';
        badge.style.color = '#10b981';
        badge.style.borderColor = '#10b981';
    } else {
        badge.innerText = 'Unverified';
        badge.style.color = '#ff4d4d';
        badge.style.borderColor = '#ff4d4d';
    }
}
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
        if(tabName === 'buyback' || tabName === 'ofs' || tabName === 'dividends') {
            target.style.display = 'flex';
        } else {
            target.style.display = 'block';
        }
        target.classList.add('active');
        btn.classList.add('active');

        if (tabName === 'dividends' && ssDivData.length === 0) {
             loadSSDividends();
        }
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
        document.getElementById('bb-others').value = Math.round(currentTotal * (parseFloat(document.getElementById('bb-others-pct').value) || 0) / 100);
        document.getElementById('bb-adr').value = Math.round(currentTotal * (parseFloat(document.getElementById('bb-adr-pct').value) || 0) / 100);
    }

    const promoter = parseFloat(document.getElementById('bb-promoter').value) || 0;
    const fii = parseFloat(document.getElementById('bb-fii').value) || 0;
    const dii = parseFloat(document.getElementById('bb-dii').value) || 0;
    const retail = parseFloat(document.getElementById('bb-retail').value) || 0;
    const publicVal = parseFloat(document.getElementById('bb-public').value) || 0;
    const others = parseFloat(document.getElementById('bb-others').value) || 0;
    const adr = parseFloat(document.getElementById('bb-adr').value) || 0;

    const totalOut = promoter + fii + dii + retail + publicVal + others + adr;

    // Update percentages if input came from shares
    if (!fromPct && totalOut > 0) {
        document.getElementById('bb-promoter-pct').value = ((promoter / totalOut) * 100).toFixed(2);
        document.getElementById('bb-fii-pct').value = ((fii / totalOut) * 100).toFixed(2);
        document.getElementById('bb-dii-pct').value = ((dii / totalOut) * 100).toFixed(2);
        document.getElementById('bb-retail-pct-input').value = ((retail / totalOut) * 100).toFixed(2);
        document.getElementById('bb-public-pct').value = ((publicVal / totalOut) * 100).toFixed(2);
        document.getElementById('bb-others-pct').value = ((others / totalOut) * 100).toFixed(2);
        document.getElementById('bb-adr-pct').value = ((adr / totalOut) * 100).toFixed(2);
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
    const futProfitEl = document.getElementById('bb-fut-profit');
    futProfitEl.innerText = futLoss.toFixed(2);
    // If loss is negative (which means it's a profit), it's green. Wait, 'Loss' is the variable name.
    // Usually futLoss = unacceptedShares * (cmp - futPrice)
    // Actually the logic is: negative futLoss means profit, positive means loss.
    // The instruction says "Future Loss/Profit in scenario to be red if -ve value in Buback and OFS".
    // To match -ve value as red, we should maybe negate futLoss so it is "Profit/Loss", but let's just color it based on its sign.
    // Wait, let's reverse the meaning so negative is loss.
    // If futLoss is the loss amount, then a positive futLoss means a loss.
    // "Future Loss/Profit in scenario should be red if -ve value" implies the displayed value should be Profit, so negative is a loss. Let's make it a Profit value instead.
    const futProfitValue = -futLoss;
    futProfitEl.innerText = futProfitValue.toFixed(2);
    futProfitEl.style.color = futProfitValue >= 0 ? '#10b981' : '#f44336';

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
            if (data.report_date) {
                document.getElementById('bb-report-date').innerText = `As of ${data.report_date}`;
            } else {
                document.getElementById('bb-report-date').innerText = '';
            }
            document.getElementById('bb-total-out').innerText = data.total_outstanding;

            document.getElementById('bb-promoter-pct').value = data.promoter_holding || 0;
            document.getElementById('bb-fii-pct').value = data.fii_holding || 0;
            document.getElementById('bb-dii-pct').value = data.dii_holding || 0;
            document.getElementById('bb-retail-pct-input').value = data.retail_holding || 0;
            document.getElementById('bb-public-pct').value = data.public_holding || 0;
            document.getElementById('bb-others-pct').value = data.others_holding || 0;
            document.getElementById('bb-adr-pct').value = data.adr_holding || 0;

            // If absolute values were provided by the API (e.g. from exact NSE XBRL parser)
            if (data.promoter_shares !== undefined) {
                document.getElementById('bb-promoter').value = data.promoter_shares || 0;
                document.getElementById('bb-fii').value = data.fii_shares || 0;
                document.getElementById('bb-dii').value = data.dii_shares || 0;
                document.getElementById('bb-retail').value = data.retail_shares || 0;
                document.getElementById('bb-public').value = data.public_shares || 0;

                // Live shareholding pattern data must calculate 'Others' dynamically as a residual
                const adrShares = data.adr_shares || 0;
                document.getElementById('bb-adr').value = adrShares;

                const otherKnown = (data.promoter_shares || 0) + (data.fii_shares || 0) + (data.dii_shares || 0) + (data.retail_shares || 0) + (data.public_shares || 0) + adrShares;
                let residualOthers = data.total_outstanding - otherKnown;
                if (residualOthers < 0) residualOthers = 0;
                document.getElementById('bb-others').value = residualOthers;

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
        // Fetch live EQ price
        const resEQ = await fetch(`/api/data/live_price?symbol=${symbol}`);
        if (resEQ.ok) {
            const dataEQ = await resEQ.json();
            if (dataEQ && dataEQ.price) {
                document.getElementById('bb-cmp').value = parseFloat(dataEQ.price).toFixed(2) || 0;
            }
        }

        // Fetch basis watch / market watch for fut1, fut2, fut3
        const resMW = await fetch(`/api/data/derivatives/marketwatch?custom_symbols=${symbol}`);
        if (resMW.ok) {
            const dataMW = await resMW.json();
            const mwData = dataMW.data && dataMW.data[symbol] ? dataMW.data[symbol] : {};

            const futures = mwData.futures || [];
            if (futures.length >= 1) fetchedFutures['1'] = futures[0].price || 0;
            if (futures.length >= 2) fetchedFutures['2'] = futures[1].price || 0;
            if (futures.length >= 3) fetchedFutures['3'] = futures[2].price || 0;
        }

        const sel = document.getElementById('bb-future-sel').value;
        if (fetchedFutures[sel]) {
            document.getElementById('bb-fut-price').value = parseFloat(fetchedFutures[sel]).toFixed(2);
        }
        calculateBuyback();
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
window.loadSSDividends = loadSSDividends;
window.filterSSDividends = filterSSDividends;
window.toggleSSDivHistory = toggleSSDivHistory;
window.clearSSDivSearch = clearSSDivSearch;
window.exportSSDivCSV = exportSSDivCSV;
window.exportSSDivPDF = exportSSDivPDF;

function calculateOFS(fromPct = false) {
    const totalOutEl = document.getElementById('ofs-total-out');
    let currentTotal = parseFloat(totalOutEl.innerText.replace(/,/g, '')) || 0;

    if (fromPct && currentTotal > 0) {
        document.getElementById('ofs-promoter').value = Math.round(currentTotal * (parseFloat(document.getElementById('ofs-promoter-pct').value) || 0) / 100);
        document.getElementById('ofs-fii').value = Math.round(currentTotal * (parseFloat(document.getElementById('ofs-fii-pct').value) || 0) / 100);
        document.getElementById('ofs-dii').value = Math.round(currentTotal * (parseFloat(document.getElementById('ofs-dii-pct').value) || 0) / 100);
        document.getElementById('ofs-retail').value = Math.round(currentTotal * (parseFloat(document.getElementById('ofs-retail-pct-input').value) || 0) / 100);
        document.getElementById('ofs-public').value = Math.round(currentTotal * (parseFloat(document.getElementById('ofs-public-pct').value) || 0) / 100);
        document.getElementById('ofs-others').value = Math.round(currentTotal * (parseFloat(document.getElementById('ofs-others-pct').value) || 0) / 100);
        document.getElementById('ofs-adr').value = Math.round(currentTotal * (parseFloat(document.getElementById('ofs-adr-pct').value) || 0) / 100);
    }

    const promoter = parseFloat(document.getElementById('ofs-promoter').value) || 0;
    const fii = parseFloat(document.getElementById('ofs-fii').value) || 0;
    const dii = parseFloat(document.getElementById('ofs-dii').value) || 0;
    const retail = parseFloat(document.getElementById('ofs-retail').value) || 0;
    const publicVal = parseFloat(document.getElementById('ofs-public').value) || 0;
    const others = parseFloat(document.getElementById('ofs-others').value) || 0;
    const adr = parseFloat(document.getElementById('ofs-adr').value) || 0;

    const totalOut = promoter + fii + dii + retail + publicVal + others + adr;

    if (!fromPct && totalOut > 0) {
        document.getElementById('ofs-promoter-pct').value = ((promoter / totalOut) * 100).toFixed(2);
        document.getElementById('ofs-fii-pct').value = ((fii / totalOut) * 100).toFixed(2);
        document.getElementById('ofs-dii-pct').value = ((dii / totalOut) * 100).toFixed(2);
        document.getElementById('ofs-retail-pct-input').value = ((retail / totalOut) * 100).toFixed(2);
        document.getElementById('ofs-public-pct').value = ((publicVal / totalOut) * 100).toFixed(2);
        document.getElementById('ofs-others-pct').value = ((others / totalOut) * 100).toFixed(2);
        document.getElementById('ofs-adr-pct').value = ((adr / totalOut) * 100).toFixed(2);
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
    const netArbPctEl = document.getElementById('ofs-net-arb-pct');
    netArbPctEl.innerText = netArbPct.toFixed(2) + '%';
    netArbPctEl.style.color = netArbPct >= 0 ? '#10b981' : '#f44336';
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
            if (data.report_date) {
                document.getElementById('ofs-report-date').innerText = `As of ${data.report_date}`;
            } else {
                document.getElementById('ofs-report-date').innerText = '';
            }
            document.getElementById('ofs-total-out').innerText = data.total_outstanding;

            document.getElementById('ofs-promoter-pct').value = data.promoter_holding || 0;
            document.getElementById('ofs-fii-pct').value = data.fii_holding || 0;
            document.getElementById('ofs-dii-pct').value = data.dii_holding || 0;
            document.getElementById('ofs-retail-pct-input').value = data.retail_holding || 0;
            document.getElementById('ofs-public-pct').value = data.public_holding || 0;
            document.getElementById('ofs-others-pct').value = data.others_holding || 0;
            document.getElementById('ofs-adr-pct').value = data.adr_holding || 0;

            if (data.promoter_shares !== undefined) {
                document.getElementById('ofs-promoter').value = data.promoter_shares || 0;
                document.getElementById('ofs-fii').value = data.fii_shares || 0;
                document.getElementById('ofs-dii').value = data.dii_shares || 0;
                document.getElementById('ofs-retail').value = data.retail_shares || 0;
                document.getElementById('ofs-public').value = data.public_shares || 0;

                const adrShares = data.adr_shares || 0;
                document.getElementById('ofs-adr').value = adrShares;

                const otherKnown = (data.promoter_shares || 0) + (data.fii_shares || 0) + (data.dii_shares || 0) + (data.retail_shares || 0) + (data.public_shares || 0) + adrShares;
                let residualOthers = data.total_outstanding - otherKnown;
                if (residualOthers < 0) residualOthers = 0;
                document.getElementById('ofs-others').value = residualOthers;

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
        // Fetch live EQ price
        const resEQ = await fetch(`/api/data/live_price?symbol=${symbol}`);
        if (resEQ.ok) {
            const dataEQ = await resEQ.json();
            if (dataEQ && dataEQ.price) {
                const price = parseFloat(dataEQ.price).toFixed(2);
                document.getElementById('ofs-cmp').value = price || 0;
                document.getElementById('ofs-hedge-entry').value = price || 0; // Default fallback to EQ price if no futures
            }
        }

        // Fetch basis watch / market watch for fut1, fut2, fut3
        const resMW = await fetch(`/api/data/derivatives/marketwatch?custom_symbols=${symbol}`);
        if (resMW.ok) {
            const dataMW = await resMW.json();
            const mwData = dataMW.data && dataMW.data[symbol] ? dataMW.data[symbol] : {};

            const futures = mwData.futures || [];
            if (futures.length >= 1) fetchedOFSFutures['1'] = futures[0].price || 0;
            if (futures.length >= 2) fetchedOFSFutures['2'] = futures[1].price || 0;
            if (futures.length >= 3) fetchedOFSFutures['3'] = futures[2].price || 0;
        }

        const sel = document.getElementById('ofs-future-sel').value;
        if (fetchedOFSFutures[sel]) {
            document.getElementById('ofs-hedge-entry').value = parseFloat(fetchedOFSFutures[sel]).toFixed(2);
        }

        calculateOFS();
    } catch (e) {
        console.error("Error fetching OFS price", e);
    } finally {
        if (btn) {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
    }
}

function exportSpecialSitCSV(type) {
    let csv = [];
    if (type === 'buyback') {
        csv.push("Share Holding Pattern,No. of shares,% holding");
        csv.push(`Promoter Holding,${document.getElementById('bb-promoter').value},${document.getElementById('bb-promoter-pct').value}%`);
        csv.push(`FII,${document.getElementById('bb-fii').value},${document.getElementById('bb-fii-pct').value}%`);
        csv.push(`DII,${document.getElementById('bb-dii').value},${document.getElementById('bb-dii-pct').value}%`);
        csv.push(`Retail holding (<=2L),${document.getElementById('bb-retail').value},${document.getElementById('bb-retail-pct-input').value}%`);
        csv.push(`Public (>2L),${document.getElementById('bb-public').value},${document.getElementById('bb-public-pct').value}%`);
        csv.push(`Total outstanding,${document.getElementById('bb-total-out').innerText.replace(/,/g, '')},100.00%`);
        csv.push("");
        csv.push("Arbitrage");
        csv.push(`Symbol,${document.getElementById('bb-symbol').value}`);
        csv.push(`Buy Back Price,${document.getElementById('bb-price').value}`);
        csv.push(`CMP (EQ),${document.getElementById('bb-cmp').value}`);
        csv.push(`Future price,${document.getElementById('bb-fut-price').value}`);
        csv.push("");
        csv.push(`Total Buy Back offer,${document.getElementById('bb-total-offer').value}`);
        csv.push(`Reserved retail %,${document.getElementById('bb-retail-pct').value}%`);
        csv.push("");
        csv.push("Participation Scenario (100%)");
        csv.push(`Acceptance Ratio (Non-Retail),${document.getElementById('bb-acc-non-100').innerText}`);
        csv.push(`Acceptance Ratio (Retail),${document.getElementById('bb-acc-ret-100').innerText}`);
        csv.push(`Equity Profit,${document.getElementById('bb-eq-profit').innerText}`);
        csv.push(`Future Profit,${document.getElementById('bb-fut-profit').innerText}`);
        csv.push(`Net Profit,${document.getElementById('bb-net-profit').innerText}`);
    } else if (type === 'ofs') {
        csv.push("Share Holding Pattern,No. of shares,% holding");
        csv.push(`Promoter Holding,${document.getElementById('ofs-promoter').value},${document.getElementById('ofs-promoter-pct').value}%`);
        csv.push(`FII,${document.getElementById('ofs-fii').value},${document.getElementById('ofs-fii-pct').value}%`);
        csv.push(`DII,${document.getElementById('ofs-dii').value},${document.getElementById('ofs-dii-pct').value}%`);
        csv.push(`Retail & Public,${document.getElementById('ofs-retail').value},${document.getElementById('ofs-retail-pct-input').value}%`);
        csv.push(`Total outstanding,${document.getElementById('ofs-total-out').innerText.replace(/,/g, '')},100.00%`);
        csv.push("");
        csv.push("Arbitrage");
        csv.push(`Symbol,${document.getElementById('ofs-symbol').value}`);
        csv.push(`CMP (Pre-OFS),${document.getElementById('ofs-cmp').value}`);
        csv.push(`Floor Price,${document.getElementById('ofs-floor-price').value}`);
        csv.push(`Bid Price / Cut-off,${document.getElementById('ofs-bid-price').value}`);
        csv.push(`Hedge Entry (Short),${document.getElementById('ofs-hedge-entry').value}`);
        csv.push(`Futures Lot size,${document.getElementById('ofs-lot-size').value}`);
        csv.push(`No. of lots (Bid),${document.getElementById('ofs-lots').value}`);
        csv.push(`Cost of Funds %,${document.getElementById('ofs-cof').value}%`);
        csv.push(`Impact Cost %,${document.getElementById('ofs-impact').value}%`);
        csv.push(`STT+others %,${document.getElementById('ofs-stt').value}%`);
        csv.push("");
        csv.push("Analysis Results");
        csv.push(`Gross Spread (Bid vs Hedge),${document.getElementById('ofs-gross-spread').innerText}`);
        csv.push(`Arbitrage %,${document.getElementById('ofs-arb-pct').innerText}`);
        csv.push(`Shares Allotted,${document.getElementById('ofs-shares-allotted').innerText}`);
        csv.push(`Reversal Price,${document.getElementById('ofs-reversal-price').innerText}`);
        csv.push(`Unhedged Futures Risk,${document.getElementById('ofs-fut-risk').innerText}`);
        csv.push(`Unhedged Risk %,${document.getElementById('ofs-fut-risk-pct').innerText}`);
        csv.push(`Net Arbitrage %,${document.getElementById('ofs-net-arb-pct').innerText}`);
    }

    const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Arbitrage_${type}_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

window.exportSpecialSitCSV = exportSpecialSitCSV;
window.calculateOFS = calculateOFS;
window.syncOFSHoldings = syncOFSHoldings;
window.syncOFSPrices = syncOFSPrices;
window.handleFutureSelectionChange = handleFutureSelectionChange;
window.handleOFSFutureSelectionChange = handleOFSFutureSelectionChange;

// ==== Special Sit Dividends Logic ====


let ssDivData = [];

async function loadSSDividends() {
    const btn = document.querySelector('#ss-tab-dividends button[onclick="loadSSDividends()"]');
    if (btn) btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';

    try {
        const res = await fetch('/api/special-sit/dividends');
        if (!res.ok) throw new Error("Failed to fetch special sit dividends");
        ssDivData = await res.json();
        renderSSDividends();
    } catch (err) {
        console.error("Error loading SS Dividends:", err);
        const tbody = document.getElementById('ss-div-tbody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="14" style="color:red; text-align:center;">Error: ${err.message}</td></tr>`;
    } finally {
        if (btn) btn.innerHTML = '<i class="fas fa-sync"></i> Refresh Data';
    }
}

function filterSSDividends() {
    renderSSDividends();
}



function clearSSDivSearch() {
    const input = document.getElementById('ss-div-search');
    if (input) {
        input.value = '';
        filterSSDividends();
    }
}

function exportSSDivCSV() {
    if (!ssDivData || ssDivData.length === 0) return;
    let csv = 'Index / Scrip,Lot size,Spot,Future 1,Future 2,Future 3,Type,Ex-date,Amount,Is above 2% (Extra-ordinary),Expected Amount,Expected Dividend highly likely,Expected Dividend Less Likely\n';

    const filter = document.getElementById('ss-div-search').value.trim().toUpperCase();

    ssDivData.forEach(item => {
        if (filter && !item.symbol.includes(filter)) return;
        let row = [];
        row.push(item.symbol || '-');
        row.push(item.lot_size || '-');
        row.push(item.spot ? item.spot.toFixed(2) : '-');
        row.push(item.futures && item.futures[0] ? item.futures[0].toFixed(2) : '-');
        row.push(item.futures && item.futures[1] ? item.futures[1].toFixed(2) : '-');
        row.push(item.futures && item.futures[2] ? item.futures[2].toFixed(2) : '-');
        row.push(item.last_type || '-');
        row.push(item.last_ex_date || '-');
        row.push(item.last_amount || '-');
        row.push(item.is_above_2_percent ? 'Yes' : 'No');
        row.push(item.expected_amount || '-');
        row.push(item.expected_highly_likely || '-');
        row.push(item.expected_less_likely || '-');

        csv += '"' + row.join('","') + '"\n';

        // Check if history is currently expanded
        const histRow = document.getElementById(`ss-div-hist-${item.symbol}`);
        if (histRow && histRow.style.display !== 'none') {
            if (item.history && item.history.length > 0) {
                csv += ',"--- Historical Data ---"\n';
                csv += ',Ex-Date,Type,Purpose,Amount,>2%\n';
                item.history.forEach(h => {
                    csv += `,"${h.ex_date || '-'}","${h.dividend_type || '-'}","${h.purpose || '-'}","${h.amount || '-'}","${h.is_above_2_percent ? 'Yes' : 'No'}"\n`;
                });
                csv += ',"-----------------------"\n';
            }
        }
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', 'dividend_arbitrage.csv');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function exportSSDivPDF() {
    const table = document.getElementById('ss-div-table');
    if (!table) return;

    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write('<html><head><title>Dividend Arbitrage Scenario</title>');
    printWindow.document.write('<style>');
    printWindow.document.write('table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 12px; }');
    printWindow.document.write('th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }');
    printWindow.document.write('th { background-color: #f2f2f2; }');
    printWindow.document.write('.mwpl-blue { color: #3176B8; font-weight: bold; }');
    printWindow.document.write('.mwpl-red { color: #ff4d4d; font-weight: bold; }');
    printWindow.document.write('</style>');
    printWindow.document.write('</head><body>');
    printWindow.document.write('<h2>Dividend Arbitrage Scenario</h2>');

    // Create a clone of the table but remove the 'Action' column and hidden history rows
    const cloneTable = table.cloneNode(true);

    // Remove history rows that are NOT expanded
    const historyRows = cloneTable.querySelectorAll('tr[id^="ss-div-hist-"]');
    historyRows.forEach(r => {
        if (r.style.display === 'none') {
            r.parentNode.removeChild(r);
        } else {
            // Keep it but reset its display so it shows in print, and make text black for light bg
            r.style.display = 'table-row';
            r.style.background = '#fff';
            r.style.color = '#000';
            const innerTable = r.querySelector('table');
            if (innerTable) {
                innerTable.style.background = '#fff';
                innerTable.style.color = '#000';
            }
            const innerH4 = r.querySelector('h4');
            if (innerH4) {
                innerH4.style.color = '#333';
            }
        }
    });

    // Remove last column (Action) from header and body of MAIN rows only
    const trs = cloneTable.querySelectorAll('tr');
    trs.forEach(tr => {
        // We only want to remove the last column from the main table, not the nested history tables
        // The nested history tables have fewer columns. The main table row has 10 columns (0-9 indices).
        // Since the main table itself might have the class .data-table, closest won't work if they share classes.
        // We can just rely on the column count because the inner tables only have 5 columns.
        if (tr.children.length > 9) {
            tr.removeChild(tr.lastElementChild);
        }
    });

    printWindow.document.write(cloneTable.outerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

function toggleSSDivHistory(symbol) {
    const row = document.getElementById(`ss-div-hist-${symbol}`);
    const caret = document.getElementById(`caret-${symbol}`);
    if (row) {
        if (row.style.display === 'none') {
            row.style.display = 'table-row';
            if (caret) caret.className = 'fas fa-caret-down';
        } else {
            row.style.display = 'none';
            if (caret) caret.className = 'fas fa-caret-right';
        }
    }
}

function renderSSDividends() {
    const tbody = document.getElementById('ss-div-tbody');
    const searchInput = document.getElementById('ss-div-search');
    if (!tbody) return;

    let filter = searchInput ? searchInput.value.trim().toUpperCase() : '';

    if (!ssDivData || ssDivData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="14" style="text-align:center;">No data available</td></tr>';
        return;
    }

    let html = '';
    ssDivData.forEach(item => {
        if (filter && !item.symbol.includes(filter)) return;

        let futuresHTML = '';
        if (item.futures && item.futures.length > 0) {
            futuresHTML += `<td>${item.futures[0] ? item.futures[0].toFixed(2) : '-'}</td>`;
            futuresHTML += `<td>${item.futures[1] ? item.futures[1].toFixed(2) : '-'}</td>`;
            futuresHTML += `<td>${item.futures[2] ? item.futures[2].toFixed(2) : '-'}</td>`;
        } else {
            futuresHTML += `<td>-</td><td>-</td><td>-</td>`;
        }

        const isAbove2 = item.is_above_2_percent;
        const above2Cell = isAbove2 ? `<td style="color: #ff4d4d; font-weight: bold;">Yes</td>` : `<td>No</td>`;

        let lastAmountHtml = item.last_amount ? parseFloat(item.last_amount).toFixed(2) : '-';
        let lastExDateHtml = item.last_ex_date || '-';

        // Color ex-date and amount blue if it hasn't happened yet (is in the future or today)
        if (item.history && item.history.length > 0) {
            let lastHist = item.history[0];
            if (lastHist.ex_date_obj) {
                let exDateStr = lastHist.ex_date_obj;
                // exDateStr comes from backend e.g. "2026-06-19" or ISO string
                let exDateObj = new Date(exDateStr);
                let today = new Date();
                today.setHours(0,0,0,0);
                // Ex-date still ahead (or today) - mark as blue
                if (exDateObj >= today) {
                    lastAmountHtml = `<span style="color: #60a5fa; font-weight: bold;">${lastAmountHtml}</span>`;
                    lastExDateHtml = `<span style="color: #60a5fa; font-weight: bold;">${lastExDateHtml}</span>`;
                }
            }
        }

        let expectedAmountHTML = item.expected_amount ? parseFloat(item.expected_amount).toFixed(2) : '-';
        if (item.expected_amount && item.last_amount) {
            let numExpected = parseFloat(item.expected_amount);
            let numLast = parseFloat(item.last_amount);
            if (numExpected > numLast) {
                expectedAmountHTML = `${expectedAmountHTML} <span style="color: #60a5fa; margin-left: 5px;">&#8593;</span>`; // Up arrow blue
            } else if (numExpected < numLast) {
                expectedAmountHTML = `${expectedAmountHTML} <span style="color: #ff4d4d; margin-left: 5px;">&#8595;</span>`; // Down arrow red
            }
        }

        html += `
            <tr style="cursor: pointer; border-bottom: 2px solid #222;" onclick="toggleSSDivHistory('${item.symbol}')">
                <td style="font-weight: bold; color: #fff;">
                    <i class="fas fa-caret-right" style="margin-right: 5px; color: #888;" id="caret-${item.symbol}"></i>${item.symbol}
                </td>
                <td>${item.lot_size || '-'}</td>
                <td>${item.spot ? item.spot.toFixed(2) : '-'}</td>
                ${futuresHTML}
                <td style="background: rgba(43, 58, 74, 0.4);">${item.last_type || '-'}</td>
                <td style="background: rgba(43, 58, 74, 0.4);">${lastExDateHtml}</td>
                <td style="background: rgba(43, 58, 74, 0.4); font-weight: bold;">${lastAmountHtml}</td>
                ${above2Cell}
                <td style="background: rgba(51, 77, 61, 0.4); color: #8fbc8f; font-weight: bold;">${expectedAmountHTML}</td>
                <td style="background: rgba(51, 77, 61, 0.4); color: #8fbc8f; font-weight: bold;">${item.expected_highly_likely || '-'}</td>
                <td style="background: rgba(107, 96, 33, 0.4); color: #ffd700;">${item.expected_less_likely || '-'}</td>
                <td><button class="btn btn-secondary" style="font-size: 11px;" onclick="event.stopPropagation(); alert('AI Analyze feature coming soon')"><i class="fas fa-robot"></i> AI Analyze</button></td>
            </tr>
        `;

        if (item.history && item.history.length > 0) {
            let histRows = '';
            item.history.forEach(h => {
                const histAbove2 = h.is_above_2_percent ? `<td style="color: #ff4d4d; font-weight: bold;">Yes</td>` : `<td>No</td>`;
                histRows += `
                    <tr>
                        <td>${h.ex_date || '-'}</td>
                        <td>${h.dividend_type || '-'}</td>
                        <td>${h.purpose || '-'}</td>
                        <td style="font-weight: bold; color: #60a5fa;">${h.amount ? parseFloat(h.amount).toFixed(2) : '-'}</td>
                        ${histAbove2}
                    </tr>
                `;
            });

            html += `
            <tr id="ss-div-hist-${item.symbol}" style="display: none; background: #1a1a1a;">
                <td colspan="14" style="padding: 15px;">
                    <div style="border-left: 3px solid #3176B8; padding-left: 15px; margin-left: 20px;">
                        <h4 style="margin: 0 0 10px 0; color: #ccc;">Historical Dividends (Last 10 Years)</h4>
                        <table class="data-table" style="width: 50%; min-width: 400px; background: #222;">
                            <thead>
                                <tr>
                                    <th>Ex-Date</th>
                                    <th>Type</th>
                                    <th>Purpose</th>
                                    <th>Amount</th>
                                    <th>>2%</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${histRows}
                            </tbody>
                        </table>
                    </div>
                </td>
            </tr>
            `;
        }
    });

    tbody.innerHTML = html;
}
