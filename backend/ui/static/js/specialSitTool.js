// Javascript for Special Situation Arb

let ssDivData = [];
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

    // Core inputs from Excel
    const cmp = parseFloat(document.getElementById('ofs-cmp').value) || 0;
    const floorPrice = parseFloat(document.getElementById('ofs-floor-price').value) || 0;
    const bidPrice = parseFloat(document.getElementById('ofs-bid-price').value) || 0;
    let allotmentRatio = parseFloat(document.getElementById('ofs-allotment-ratio').value) || 0;
    const hedgeEntry = parseFloat(document.getElementById('ofs-hedge-entry').value) || 0;
    const lotSize = parseFloat(document.getElementById('ofs-lot-size').value) || 0;
    let lotsFloor = parseFloat(document.getElementById('ofs-lots').value) || 0;

    // Spread & Arb %
    const grossSpread = hedgeEntry - bidPrice;
    document.getElementById('ofs-gross-spread').innerText = grossSpread.toFixed(2);

    let arbPct = 0;
    if (bidPrice > 0) {
        arbPct = (grossSpread / bidPrice) * 100;
    }
    document.getElementById('ofs-arb-pct').innerText = arbPct.toFixed(2);

    // Total Shares calculations
    const sharesOnOffer = parseFloat(document.getElementById('ofs-shares-on-offer').value) || 0;
    const greenshoe = parseFloat(document.getElementById('ofs-greenshoe').value) || 0;
    const reservedRetailPct = parseFloat(document.getElementById('ofs-retail-pct').value) || 10;

    const totalSharesIncludingGreenshoe = sharesOnOffer + greenshoe;
    const reservedRetailShares = totalSharesIncludingGreenshoe * (reservedRetailPct / 100);
    document.getElementById('ofs-reserved-retail').innerText = reservedRetailShares.toFixed(1);

    const totalInstShares = totalSharesIncludingGreenshoe - reservedRetailShares;
    document.getElementById('ofs-total-institutional').innerText = totalInstShares.toFixed(1);

    // --- Bid Allotment Matrix ---
    const tbody = document.getElementById('ofs-matrix-body');
    let totalSupplyRemaining = totalInstShares;
    let firstRowAllotmentShares = 0;
    let firstRowAllotmentPct = 0;

    if (tbody) {
        const rows = tbody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            const priceInput = row.querySelector('.ofs-matrix-price');
            const qtyInput = row.querySelector('.ofs-matrix-qty');
            const cumulInput = row.querySelector('.ofs-matrix-cumul');
            const supplyCell = row.querySelector('.ofs-matrix-supply');
            const allotPctCell = row.querySelector('.ofs-matrix-allot-pct');
            const allotSharesCell = row.querySelector('.ofs-matrix-allot-shares');

            const qtyBid = parseFloat(qtyInput.value) || 0;
            const cumulQty = parseFloat(cumulInput.value) || 0;

            // "total supply is total available shares, so even in 1st cell of total supply you have to take the available shares for institutional"
            // "and next available supply should be cumulative of above minus available supply of above"
            // This means supply strictly equals totalSupplyRemaining.
            let supplyForThisLevel = Math.max(0, totalSupplyRemaining);
            supplyCell.innerText = supplyForThisLevel.toLocaleString();

            // Determine incremental demand at this price level to avoid double counting cumulQty
            let incrementalDemand = cumulQty;
            if (index > 0) {
                const prevRow = rows[index - 1];
                const prevCumulInput = prevRow.querySelector('.ofs-matrix-cumul');
                const prevCumul = parseFloat(prevCumulInput.value) || 0;
                incrementalDemand = Math.max(0, cumulQty - prevCumul);
            }

            let allotPct = 0;
            if (incrementalDemand > 0) {
                allotPct = (supplyForThisLevel / incrementalDemand) * 100;
                if (allotPct > 100) allotPct = 100;
            }

            const sharesAllotted = Math.floor(qtyBid * (allotPct / 100));

            allotPctCell.innerText = allotPct.toFixed(2) + '%';
            allotPctCell.style.color = allotPct > 0 ? '#FFD700' : '#888';
            allotPctCell.style.fontWeight = allotPct > 0 ? 'bold' : 'normal';
            allotSharesCell.innerText = sharesAllotted.toLocaleString();

            // Deduct the supply USED at this price level from remaining supply
            // If supplyForThisLevel > incrementalDemand, all incrementalDemand is satisfied.
            const allocatedAtThisLevel = incrementalDemand * (allotPct / 100);
            totalSupplyRemaining = Math.max(0, totalSupplyRemaining - allocatedAtThisLevel);

            if (index === 0) {
                firstRowAllotmentShares = sharesAllotted;
                firstRowAllotmentPct = allotPct;
            }
        });
    }

    // "you need to pick the allotment ratio from the first allotment ratio"
    if (firstRowAllotmentPct > 0) {
        document.getElementById('ofs-allotment-ratio').value = firstRowAllotmentPct.toFixed(2);
        allotmentRatio = firstRowAllotmentPct;
    }

    // "no. of lots, should be auto calculated based on the shares alloted in 1st column"
    // Shares allotted in 1st column = firstRowAllotmentShares
    // No of lots = firstRowAllotmentShares / Futures Lot size
    if (lotSize > 0 && firstRowAllotmentShares > 0) {
        const calculatedLots = Math.floor(firstRowAllotmentShares / lotSize);
        document.getElementById('ofs-lots').value = calculatedLots;
        lotsFloor = calculatedLots; // Update local variable for further logic
    }

    // Total Shares Bid (before allotment)
    const totalSharesBid = lotSize * lotsFloor;

    let finalSharesAllotted = firstRowAllotmentShares;
    if (allotmentRatio > 0 && lotSize > 0 && lotsFloor > 0) {
        finalSharesAllotted = Math.floor(totalSharesBid * (allotmentRatio / 100));
    }
    document.getElementById('ofs-shares-allotted').innerText = finalSharesAllotted.toLocaleString();

    const cof = parseFloat(document.getElementById('ofs-cof').value) || 0;
    const impact = parseFloat(document.getElementById('ofs-impact').value) || 0;
    const stt = parseFloat(document.getElementById('ofs-stt').value) || 0;

    // Unhedged risk is the remaining shares that cannot be covered by the rounded down integer lot size
    const futRiskSize = Math.max(0, finalSharesAllotted - totalSharesBid);
    document.getElementById('ofs-fut-risk').innerText = futRiskSize.toFixed(2);

    const totalCosts = cof + impact + stt;
    const netArbPct = arbPct - totalCosts;
    const netArbPctEl = document.getElementById('ofs-net-arb-pct');
    netArbPctEl.innerText = netArbPct.toFixed(2);
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



async function loadSSDividends(event = null) {
    const btn = document.getElementById('btn-load-ss-div') || document.querySelector('#ss-tab-dividends button[onclick*="loadSSDividends"]');
    if (btn) btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';

    try {
        const res = await fetch('/api/special-sit/dividends');
        if (!res.ok) throw new Error("Failed to fetch special sit dividends");
        const payload = await res.json();

        if (payload.date) {
            document.getElementById('ss-div-date-display').innerText = `(EQ Data: ${payload.eq_date})`;
        } else if (payload.eq_date) {
            document.getElementById('ss-div-date-display').innerText = `(EQ Data: ${payload.eq_date})`;
        }

        ssDivData = payload.data || payload; // fallback for older format if necessary

        // Apply overrides from localStorage
        let overrides = JSON.parse(localStorage.getItem('ssDivOverrides') || '{}');

        // Purge stale "Amount declared..." overrides if the backend has successfully resolved an ex_date
        Object.keys(overrides).forEach(sym => {
            if (overrides[sym] && overrides[sym].expected_less_likely === "Amount declared, date not yet announced") {
                 let beItem = ssDivData.find(x => x.symbol === sym);
                 if (beItem && beItem.last_ex_date !== 'Record date not yet declared' && beItem.last_ex_date !== '-') {
                      delete overrides[sym].expected_less_likely;
                      if (Object.keys(overrides[sym]).length === 0) delete overrides[sym];
                 }
            }
        });
        localStorage.setItem('ssDivOverrides', JSON.stringify(overrides));

        ssDivData.forEach(item => {
            if (item._original_is_above_2_percent === undefined) {
                item._original_is_above_2_percent = item.is_above_2_percent;
            }
            if (overrides[item.symbol]) {
                const o = overrides[item.symbol];
                if (o.expected_amount !== undefined) item.expected_amount = o.expected_amount;
                if (o._edited_expected_amount !== undefined) item._edited_expected_amount = o._edited_expected_amount;
                if (o.expected_highly_likely !== undefined) item.expected_highly_likely = o.expected_highly_likely;
                if (o.expected_less_likely !== undefined) item.expected_less_likely = o.expected_less_likely;
                if (o.is_above_2_percent !== undefined) item.is_above_2_percent = o.is_above_2_percent;
                if (o.note !== undefined) item.note = o.note;
            }
        });

        // Extract unique sectors and populate dropdown
        const sectorMenu = document.getElementById('ss-div-sector-menu');
        if (sectorMenu && ssDivData.length > 0) {
            const sectors = [...new Set(ssDivData.map(item => item.sector || '-'))].filter(s => s && s !== '-').sort();
            sectorMenu.innerHTML = sectors.map(s =>
                `<label><input type="checkbox" value="${s}" onchange="filterSSDividends()"> ${s}</label>`
            ).join('');
        }

        renderSSDividends();
    } catch (err) {
        console.error("Error loading SS Dividends:", err);
        const tbody = document.getElementById('ss-div-tbody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="16" style="color:red; text-align:center;">Error: ${err.message}</td></tr>`;
    } finally {
        if (btn) btn.innerHTML = '<i class="fas fa-sync"></i> Refresh Data';
    }
}

function filterSSDividends() {
    window._ssDivUpcomingFilter = Array.from(document.querySelectorAll('#ss-div-upcoming-dropdown input[type="checkbox"]:checked')).map(cb => cb.value);
    renderSSDividends();
}

function checkUpcomingMatch(bmDateStr, selectedUpcoming) {
    if (!bmDateStr || !selectedUpcoming || selectedUpcoming.length === 0) return false;
    const today = new Date();
    today.setHours(0,0,0,0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const thisWeekEnd = new Date(today);
    thisWeekEnd.setDate(thisWeekEnd.getDate() + (6 - thisWeekEnd.getDay()));
    const nextWeekStart = new Date(thisWeekEnd);
    nextWeekStart.setDate(nextWeekStart.getDate() + 1);
    const nextWeekEnd = new Date(nextWeekStart);
    nextWeekEnd.setDate(nextWeekEnd.getDate() + 6);

    const parts = bmDateStr.split('T')[0].split('-');
    if (parts.length !== 3) return false;

    // Create local date to avoid timezone shift from YYYY-MM-DD ISO format
    const bmDate = new Date(parts[0], parts[1] - 1, parts[2]);
    bmDate.setHours(0,0,0,0);

    if (selectedUpcoming.includes('Today') && bmDate.getTime() === today.getTime()) return true;
    if (selectedUpcoming.includes('Tomorrow') && bmDate.getTime() === tomorrow.getTime()) return true;
    if (selectedUpcoming.includes('This Week') && bmDate >= today && bmDate <= thisWeekEnd) return true;
    if (selectedUpcoming.includes('Next Week') && bmDate >= nextWeekStart && bmDate <= nextWeekEnd) return true;
    if (selectedUpcoming.includes('This Month') && bmDate.getMonth() === today.getMonth() && bmDate.getFullYear() === today.getFullYear()) return true;
    return false;
}




function clearSSDivSearch() {
    const input = document.getElementById('ss-div-search');
    if (input) {
        input.value = '';
        filterSSDividends();
    }
}

function exportSSDivXLS() {
    if (!ssDivData || ssDivData.length === 0) return;
    const eqDateEl = document.getElementById('ss-div-date-display');
    const eqDateStr = eqDateEl && eqDateEl.textContent ? eqDateEl.textContent.trim() : '';

    let wsData = [];
    wsData.push(["Turtle Terminal vishal@underroot.xyz | +91 9867215754"]);
    if (eqDateStr) wsData.push(["Date:", eqDateStr]);
    wsData.push([]);

    // Main Headers
    wsData.push([
        'Index / Scrip', 'Sector', 'Lot size', 'Spot', 'Future 1', 'Future 2', 'Future 3',
        'Type', 'Ex-date', 'Amount', 'Upcoming Meeting', 'Broadcast Date & Time',
        'Is above 2% (Extra-ordinary)', 'Expected Amount', 'Expected Dividend highly likely',
        'Expected Dividend Less Likely', 'Note'
    ]);

    const filter = document.getElementById('ss-div-search').value.trim().toUpperCase();

    const sectorCheckboxes = document.querySelectorAll('#ss-div-sector-dropdown input[type="checkbox"]:checked');
    const selectedSectors = Array.from(sectorCheckboxes).map(cb => cb.value);

    const upcomingCheckboxes = document.querySelectorAll('#ss-div-upcoming-dropdown input[type="checkbox"]:checked');
    const exportSelectedUpcoming = Array.from(upcomingCheckboxes).map(cb => cb.value);

    const monthCheckboxes = document.querySelectorAll('#ss-div-month-dropdown input[type="checkbox"]:checked');
    const selectedMonths = Array.from(monthCheckboxes).map(cb => cb.parentElement.textContent.trim());

    ssDivData.forEach(item => {
        if (filter && !item.symbol.includes(filter)) return;

        // Filter by Ex-date Status
        const showExAnnounced = document.getElementById('ss-div-filter-ex-announced') ? document.getElementById('ss-div-filter-ex-announced').checked : true;
        const showExAwaited = document.getElementById('ss-div-filter-ex-awaited') ? document.getElementById('ss-div-filter-ex-awaited').checked : true;

        let exDateObj = item.expected_highly_likely || '';
        let isAwaited = false;
        let isAnnounced = false;

        // Define 'Announced' as having a real ex-date coming up or already passed
        // Define 'Awaited' as having an intimation/board meeting but 'not yet declared'
        if (item.history && item.history.length > 0) {
            let latestHistory = item.history[0];
            if (latestHistory.ex_date && latestHistory.ex_date.toLowerCase().includes('not yet declared')) {
                isAwaited = true;
            } else if (latestHistory.ex_date) {
                isAnnounced = true;
            }
        }

        // Also check the main highly likely column
        if (exDateObj.includes('Announced:') || exDateObj.includes('Announced')) {
            isAnnounced = true;
        }

        // If it's pure forecasting (no history and no 'Announced' tag), we might default to showing it if Awaited is checked,
        // but wait, 'Awaited' strictly means we know it's coming (board meeting happened).
        // Strict logic for "Ex-Awaited": amount declared, but no ex-date yet.
        // The backend sends 'Record date not yet declared' as ex_date string, or ex_date_obj is null.
        let isStrictAwaited = false;
        if (item.history && item.history.length > 0) {
            let lastHist = item.history[0];
            if (!lastHist.ex_date || lastHist.ex_date === 'Record date not yet declared') {
                isStrictAwaited = true;
            }
        }

        // Let's hide rows if user only wants Awaited and it's not Awaited.
        // If neither is checked, hide everything.
        if (!showExAnnounced && !showExAwaited) return;

        // If they want exclusively announced, and this is awaited, filter out.
        if (showExAnnounced && !showExAwaited && isStrictAwaited) return;

        // If they want exclusively awaited, and this is announced (or just a forecast), filter out.
        if (showExAwaited && !showExAnnounced && !isStrictAwaited) return;

        // Sector filtering
        if (selectedSectors.length > 0 && (!item.sector || !selectedSectors.includes(item.sector))) {
            return;
        }

        if (exportSelectedUpcoming.length > 0) {
            if (!checkUpcomingMatch(item.board_meeting_date, exportSelectedUpcoming)) return;
        }

        const selectedUpcoming = window._ssDivUpcomingFilter || [];
        if (selectedUpcoming.length > 0) {
            if (!checkUpcomingMatch(item.board_meeting_date, selectedUpcoming)) return;
        }

        // Month filtering based on expected_highly_likely date
        if (selectedMonths.length > 0) {
            let dateStr = item.expected_highly_likely || '';
            if (!dateStr || dateStr === '-') return; // Filter out if no valid date

            if (dateStr.includes('Announced')) {
                if (dateStr.includes('Announced:')) {
                    dateStr = dateStr.replace('Announced: ', '').trim();
                } else {
                    return;
                }
            }

            const parts = dateStr.split('-');
            if (parts.length >= 2) {
                const mPart = parts[1];
                let extractedMonthName = "";
                const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
                if (!isNaN(mPart)) {
                    let mIndex = parseInt(mPart, 10) - 1;
                    if (mIndex >= 0 && mIndex < 12) {
                        extractedMonthName = monthNames[mIndex];
                    }
                } else {
                    let mStr = mPart.substring(0, 3).toLowerCase();
                    const found = monthNames.find(mn => mn.toLowerCase().startsWith(mStr));
                    if (found) extractedMonthName = found;
                }
                if (!selectedMonths.includes(extractedMonthName)) return;
            } else {
                return;
            }
        }

        let row = [];
        row.push(item.symbol || '-');
        row.push(item.sector || '-');
        row.push(item.lot_size || '-');
        row.push(item.spot ? item.spot.toFixed(2) : '-');
        row.push(item.futures && item.futures[0] && item.futures[0].price ? item.futures[0].price.toFixed(2) : '-');
        row.push(item.futures && item.futures[1] && item.futures[1].price ? item.futures[1].price.toFixed(2) : '-');
        row.push(item.futures && item.futures[2] && item.futures[2].price ? item.futures[2].price.toFixed(2) : '-');
        row.push(item.last_type || '-');
        row.push(item.last_ex_date || '-');
        row.push(item.last_amount || '-');

        let bmDateCsv = item.board_meeting_date ? item.board_meeting_date.split('T')[0] : '-';
        row.push(bmDateCsv);

        let bcastDateCsv = item.broadcast_date ? item.broadcast_date.replace('T', ' ') : '-';
        row.push(bcastDateCsv);

        row.push(item.is_above_2_percent ? 'Yes' : 'No');
        let expectedCSV = item.expected_amount ? `${item.expected_amount} (${item.expected_type || 'Interim'})` : '-';
        row.push(expectedCSV);
        row.push(item.expected_highly_likely || '-');
        row.push(item.expected_less_likely || '-');
        row.push(item.note || '-');

        wsData.push(row);

        // Add history row if available (in XLS we can just output them as indented rows)
        if (item.history && item.history.length > 0) {
            wsData.push(["", "--- Historical Data ---"]);
            wsData.push(["", "Ex-Date", "Type", "Purpose", "Amount", ">2%", "Announced Date"]);
            item.history.forEach(h => {
                let hAnnDate = h.announcement_date_obj || h.broadcast_date || '-';
                if (hAnnDate !== '-') hAnnDate = hAnnDate.split('T')[0];

                wsData.push([
                    "",
                    h.ex_date || '-',
                    h.dividend_type || '-',
                    h.purpose || '-',
                    h.amount || '-',
                    h.is_above_2_percent ? 'Yes' : 'No',
                    hAnnDate
                ]);
            });
            wsData.push(["", "-----------------------"]);
        }
    });

    const ws = XLSX.utils.aoa_to_sheet(wsData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Dividends");
    XLSX.writeFile(wb, "dividend_arbitrage.xlsx");
}

function exportSSDivPDF() {
    const table = document.getElementById('ss-div-table');
    if (!table) return;

    const eqDateEl = document.getElementById('ss-div-date-display');
    const eqDateStr = eqDateEl && eqDateEl.textContent ? eqDateEl.textContent.trim() : '';

    const printWindow = window.open('', '', 'height=800,width=1200');
    printWindow.document.write('<html><head><title>Dividend Arbitrage Scenario</title>');
    printWindow.document.write('<style>');
    printWindow.document.write('html, body { background: #1e1e1e; color: #ccc; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }');
    printWindow.document.write('h2 { color: #d4d4d4; margin-bottom: 5px; }');
    printWindow.document.write('.data-table { width: 100%; border-collapse: collapse; font-size: 9px; white-space: nowrap; color: #d4d4d4; table-layout: auto; }');
    printWindow.document.write('.data-table th, .data-table td { border: 1px solid #3e3e42; padding: 3px 5px; text-align: left; }');
    printWindow.document.write('.data-table th { background: #252526 !important; font-weight: normal; color: #fff; }');
    printWindow.document.write('.data-table tr { background: #1e1e1e !important; }');
    printWindow.document.write('.data-table tr:nth-child(even) { background: #222222 !important; }');
    printWindow.document.write('.mwpl-blue { color: #60a5fa !important; font-weight: bold; }');
    printWindow.document.write('.mwpl-red { color: #ff4d4d !important; font-weight: bold; }');
    printWindow.document.write('@page { size: A4 landscape; margin: 0; }');
    printWindow.document.write('@media print { .no-print { display: none; } body { padding: 0; } table { page-break-inside: auto; zoom: 0.8; } tr { page-break-inside: avoid; page-break-after: auto; } thead { display: table-header-group; } }');
    printWindow.document.write('</style>');
    printWindow.document.write('</head><body>');
    printWindow.document.write('<div class="no-print" style="margin-bottom: 15px; text-align: right;"><button onclick="window.print()" style="padding: 8px 16px; background: #60a5fa; color: #fff; border: none; cursor: pointer; border-radius: 4px; font-weight: bold;">Print Document</button></div>');
    printWindow.document.write('<div style="text-align: center; font-size: 14px; color: #fff; margin-bottom: 10px; border-bottom: 1px solid #444; padding-bottom: 5px;">Turtle Terminal vishal@underroot.xyz | +91 9867215754</div>');
    printWindow.document.write('<div style="display: flex; justify-content: space-between; align-items: baseline;">');
    printWindow.document.write('<h2>Dividend Arbitrage Scenario</h2>');
    if (eqDateStr) printWindow.document.write('<div style="font-size: 14px; color: #888;">' + eqDateStr + '</div>');
    printWindow.document.write('</div>');

    // Create a clone of the table but remove the 'Action' column and hidden history rows
    const cloneTable = table.cloneNode(true);

    // Remove history rows that are NOT expanded
    const historyRows = cloneTable.querySelectorAll('tr[id^="ss-div-hist-"]');
    historyRows.forEach(r => {
        if (r.style.display === 'none') {
            r.parentNode.removeChild(r);
        } else {
            // Keep it but reset its display so it shows in print
            r.style.display = 'table-row';
            // We no longer override with white/black because we want the dark theme
            r.style.background = '#1e1e1e';
            r.style.color = '#d4d4d4';
            const innerTable = r.querySelector('table');
            if (innerTable) {
                innerTable.style.background = '#1e1e1e';
                innerTable.style.color = '#d4d4d4';
                // Add border styling for inner table to match Excel look
                innerTable.style.borderCollapse = 'collapse';
                innerTable.querySelectorAll('th, td').forEach(cell => {
                     cell.style.border = '1px solid #3e3e42';
                     cell.style.padding = '4px 8px';
                });
                innerTable.querySelectorAll('th').forEach(th => {
                     th.style.background = '#252526';
                     th.style.fontWeight = 'normal';
                });
            }
            const innerH4 = r.querySelector('h4');
            if (innerH4) {
                innerH4.style.color = '#ccc';
            }
        }
    });

    // Remove last column (Action) from header and body of MAIN rows only
    const trs = cloneTable.querySelectorAll('tr');
    trs.forEach(tr => {
        // We only want to remove the last column from the main table, not the nested history tables
        // The nested history tables have fewer columns. The main table row has > 9 columns.
        // Since the main table itself might have the class .data-table, closest won't work if they share classes.
        // We can just rely on the column count because the inner tables only have 5 columns.
        if (tr.children.length > 9) {
            tr.removeChild(tr.lastElementChild); // Remove Action column
        }
    });

    printWindow.document.write(cloneTable.outerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();

    // Automatically trigger print after a short delay to allow rendering
    setTimeout(() => {
        printWindow.focus();
        printWindow.print();
    }, 500);
}

function toggleSSDivHistory(symbol) {
    const row = document.getElementById(`ss-div-hist-${symbol}`);
    const caret = document.getElementById(`caret-${symbol}`);
    if (row) {
        if (row.style.display === 'none') {
            row.style.display = 'table-row';
            if (caret) caret.innerHTML = '&#9660;'; // Downward triangle ▼
        } else {
            row.style.display = 'none';
            if (caret) caret.innerHTML = '&#9654;'; // Rightward triangle ▶
        }
    }
}



function updateSSDivData(symbol, field, value) {
    if (!ssDivData) return;
    const item = ssDivData.find(x => x.symbol === symbol);
    if (item) {
        if (field === 'is_above_2_percent') {
            const lowerVal = value.trim().toLowerCase();
            const originalVal = (item._original_is_above_2_percent === true || item._original_is_above_2_percent === 'Yes') ? 'yes' : 'no';

            if (lowerVal === originalVal) {
                // Reverted to original, clear override
                let overrides = JSON.parse(localStorage.getItem('ssDivOverrides') || '{}');
                if (overrides[symbol]) {
                    delete overrides[symbol]['is_above_2_percent'];
                    if (Object.keys(overrides[symbol]).length === 0) delete overrides[symbol];
                    localStorage.setItem('ssDivOverrides', JSON.stringify(overrides));
                }
                item.is_above_2_percent = (originalVal === 'yes');
                return; // Stop here so it doesn't save to localstorage below
            } else {
                item.is_above_2_percent = (lowerVal === 'yes' || lowerVal === 'true' || lowerVal === '1');
            }
        } else if (field === 'expected_amount') {
            // Check if they effectively reverted to the original backend value
            let originalItemHtml = (item.expected_amount ? `${parseFloat(item.expected_amount).toFixed(2)} <span style="font-size: 0.8em; color: #aaa;">(${item.expected_type || 'Interim'})</span>` : '-').replace(/<[^>]*>?/gm, '').trim();
            let cleanedVal = value.replace(/<[^>]*>?/gm, '').replace(/\*/g, '').trim(); // Remove tags and our own asterisk
            let num = value.replace(/[^0-9.]/g, '');

            if (cleanedVal === originalItemHtml || cleanedVal === (item.expected_amount ? parseFloat(item.expected_amount).toFixed(2) : '-')) {
                // Reverted to original, clear override
                delete item._edited_expected_amount;
                if (num) {
                    item.expected_amount = parseFloat(num);
                }
            } else {
                if (num) {
                   item.expected_amount = parseFloat(num);
                   // Store cleanly without asterisks so it doesn't duplicate
                   item._edited_expected_amount = value.replace(/<span[^>]*class=["']asterisk-mark["'][^>]*>\*<\/span>/gi, '').replace(/\*/g, '').trim();
                } else {
                   item.expected_amount = null;
                   item._edited_expected_amount = value.replace(/<span[^>]*class=["']asterisk-mark["'][^>]*>\*<\/span>/gi, '').replace(/\*/g, '').trim();
                }
            }
        } else {
            if (field === 'expected_highly_likely' && typeof value === 'string') {
                // Strip out the extra-ordinary threshold text if it got captured by innerText during edit
                value = value.split('\n(Extra-ordinary')[0].trim();
            }
            item[field] = value;
        }

        // Persist to localStorage
        let overrides = JSON.parse(localStorage.getItem('ssDivOverrides') || '{}');
        if (!overrides[symbol]) overrides[symbol] = {};

        if (field === 'expected_amount') {
            overrides[symbol]['expected_amount'] = item.expected_amount;
            overrides[symbol]['_edited_expected_amount'] = item._edited_expected_amount;
        } else {
            overrides[symbol][field] = value;
        }
        localStorage.setItem('ssDivOverrides', JSON.stringify(overrides));
    }
}
function renderSSDividends() {
    const tbody = document.getElementById('ss-div-tbody');
    const searchInput = document.getElementById('ss-div-search');

    // Update Future Headers with Expiry Dates
    if (ssDivData && ssDivData.length > 0) {
        // Find the first item with valid futures
        const itemWithFutures = ssDivData.find(item => item.futures && item.futures.length > 0);
        if (itemWithFutures) {
            const f1 = itemWithFutures.futures[0];
            const f2 = itemWithFutures.futures[1];
            const f3 = itemWithFutures.futures[2];

            const th1 = document.getElementById('ss-div-fut1-th');
            const th2 = document.getElementById('ss-div-fut2-th');
            const th3 = document.getElementById('ss-div-fut3-th');

            if (th1) th1.innerHTML = 'Future 1' + (f1 && f1.expiry ? '<br><small style="color: #60a5fa; font-weight: normal;">' + f1.expiry + '</small>' : '');
            if (th2) th2.innerHTML = 'Future 2' + (f2 && f2.expiry ? '<br><small style="color: #60a5fa; font-weight: normal;">' + f2.expiry + '</small>' : '');
            if (th3) th3.innerHTML = 'Future 3' + (f3 && f3.expiry ? '<br><small style="color: #60a5fa; font-weight: normal;">' + f3.expiry + '</small>' : '');
        }
    }
    if (!tbody) return;

    let filter = searchInput ? searchInput.value.trim().toUpperCase() : '';

    // Get selected months
    const monthCheckboxes = document.querySelectorAll('#ss-div-month-dropdown input[type="checkbox"]:checked');
    const selectedMonths = Array.from(monthCheckboxes).map(cb => cb.parentElement.textContent.trim()); // Values are full month names

    // Get selected sectors
    const sectorCheckboxes = document.querySelectorAll('#ss-div-sector-dropdown input[type="checkbox"]:checked');
    const selectedSectors = Array.from(sectorCheckboxes).map(cb => cb.value);

    if (!ssDivData || ssDivData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="16" style="text-align:center;">No data available</td></tr>';
        return;
    }

    let html = '';
    ssDivData.forEach(item => {
        if (filter && !item.symbol.includes(filter)) return;


        // Filter by Ex-date Status
        const showExAnnounced = document.getElementById('ss-div-filter-ex-announced') ? document.getElementById('ss-div-filter-ex-announced').checked : true;
        const showExAwaited = document.getElementById('ss-div-filter-ex-awaited') ? document.getElementById('ss-div-filter-ex-awaited').checked : true;

        let exDateObj = item.expected_highly_likely || '';
        let isAwaited = false;
        let isAnnounced = false;

        // Define 'Announced' as having a real ex-date coming up or already passed
        // Define 'Awaited' as having an intimation/board meeting but 'not yet declared'
        if (item.history && item.history.length > 0) {
            let latestHistory = item.history[0];
            if (latestHistory.ex_date && latestHistory.ex_date.toLowerCase().includes('not yet declared')) {
                isAwaited = true;
            } else if (latestHistory.ex_date) {
                isAnnounced = true;
            }
        }

        // Also check the main highly likely column
        if (exDateObj.includes('Announced:') || exDateObj.includes('Announced')) {
            isAnnounced = true;
        }

        // If it's pure forecasting (no history and no 'Announced' tag), we might default to showing it if Awaited is checked,
        // but wait, 'Awaited' strictly means we know it's coming (board meeting happened).
        // Strict logic for "Ex-Awaited": amount declared, but no ex-date yet.
        // The backend sends 'Record date not yet declared' as ex_date string, or ex_date_obj is null.
        let isStrictAwaited = false;
        if (item.history && item.history.length > 0) {
            let lastHist = item.history[0];
            if (!lastHist.ex_date || lastHist.ex_date.toLowerCase().includes('not yet declared')) {
                isStrictAwaited = true;
            }
        }

        // Let's hide rows if user only wants Awaited and it's not Awaited.
        // If neither is checked, hide everything.
        if (!showExAnnounced && !showExAwaited) return;

        // If they want exclusively announced, and this is awaited, filter out.
        if (showExAnnounced && !showExAwaited && isStrictAwaited) return;

        // If they want exclusively awaited, and this is announced (or just a forecast), filter out.
        if (showExAwaited && !showExAnnounced && !isStrictAwaited) return;

        // Sector filtering
        if (selectedSectors.length > 0 && (!item.sector || !selectedSectors.includes(item.sector))) {
            return;
        }

        const selectedUpcoming = window._ssDivUpcomingFilter || [];
        if (selectedUpcoming.length > 0) {
            if (!checkUpcomingMatch(item.board_meeting_date, selectedUpcoming)) return;
        }

        // Month filtering based on expected_highly_likely date
        if (selectedMonths.length > 0) {
            let dateStr = item.expected_highly_likely || '';
            if (!dateStr || dateStr === '-') return; // Filter out if no valid date

            // Handle "Announced" prefix
            if (dateStr.includes('Announced')) {
                if (dateStr.includes('Announced:')) {
                    dateStr = dateStr.replace('Announced: ', '').trim();
                } else {
                    return; // Invalid format
                }
            }

            const parts = dateStr.split('-');
            let targetMonth = null;
            if (parts.length === 3) {
               // DD-MM-YYYY format
               targetMonth = parts[1];
            } else if (parts.length === 2 && isNaN(parts[1])) {
               // DD-Mon format
               targetMonth = parts[1];
            }

            if (targetMonth) {
                const monthMap = {
                    'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April',
                    'May': 'May', 'Jun': 'June', 'Jul': 'July', 'Aug': 'August',
                    'Sep': 'September', 'Oct': 'October', 'Nov': 'November', 'Dec': 'December',
                    '01': 'January',
                    '02': 'February',
                    '03': 'March',
                    '04': 'April',
                    '05': 'May',
                    '06': 'June',
                    '07': 'July',
                    '08': 'August',
                    '09': 'September',
                    '10': 'October',
                    '11': 'November',
                    '12': 'December'
                };

                const fullMonth = monthMap[targetMonth] || targetMonth;

                if (!selectedMonths.includes(fullMonth)) return;
            } else {
                return; // Unparseable, filter out
            }
        }

        let futuresHTML = '';
        if (item.futures && item.futures.length > 0) {
            const f1 = item.futures[0];
            const f2 = item.futures[1];
            const f3 = item.futures[2];
            futuresHTML += `<td>${f1 && f1.price ? f1.price.toFixed(2) : '-'}</td>`;
            futuresHTML += `<td>${f2 && f2.price ? f2.price.toFixed(2) : '-'}</td>`;
            futuresHTML += `<td>${f3 && f3.price ? f3.price.toFixed(2) : '-'}</td>`;
        } else {
            futuresHTML += `<td>-</td><td>-</td><td>-</td>`;
        }

        // Fix string "No" evaluating to true
        const isAbove2 = item.is_above_2_percent === true || item.is_above_2_percent === 'Yes';
        // User requested a dropdown instead of accidental click to toggle Yes/No
        const overrideColor = isAbove2 ? "color: #ff4d4d; font-weight: bold; background: rgba(255,0,0,0.1);" : "";


        let manualAsterisk = "";
        let overrides = JSON.parse(localStorage.getItem('ssDivOverrides') || '{}');
        if (overrides[item.symbol] && overrides[item.symbol]['is_above_2_percent'] !== undefined) {
            let currentOverride = overrides[item.symbol]['is_above_2_percent'];
            let currentOverrideLower = (currentOverride === true || String(currentOverride).toLowerCase() === 'yes' || String(currentOverride).toLowerCase() === 'true') ? 'yes' : 'no';
            const originalValLower = (item._original_is_above_2_percent === true || String(item._original_is_above_2_percent).toLowerCase() === 'yes' || String(item._original_is_above_2_percent).toLowerCase() === 'true') ? 'yes' : 'no';

            if (currentOverrideLower !== originalValLower) {
                 manualAsterisk = ' <span class="asterisk-mark" style="color: #ffeb3b; font-size: 1.2em; font-weight: bold; margin-left: 4px;" title="Manually Edited">*</span>';
            } else {
                 delete overrides[item.symbol]['is_above_2_percent'];
                 if (Object.keys(overrides[item.symbol]).length === 0) delete overrides[item.symbol];
                 localStorage.setItem('ssDivOverrides', JSON.stringify(overrides));
            }
        }


        const above2Cell = `<td style="${overrideColor} padding: 0;" onclick="event.stopPropagation();">
            <div style="display: flex; align-items: center; width: 100%;">
                <select style="background: transparent; color: inherit; border: none; font-weight: inherit; outline: none; flex-grow: 1; cursor: pointer; padding-left: 5px;" onchange="updateSSDivData('${item.symbol}', 'is_above_2_percent', this.value); renderSSDividends();">
                    <option style="background: #1e1e1e; color: #fff;" value="" ${item.is_above_2_percent !== true && item.is_above_2_percent !== false && item.is_above_2_percent !== 'Yes' && item.is_above_2_percent !== 'No' ? 'selected' : ''}></option>
                    <option style="background: #1e1e1e; color: #fff;" value="No" ${item.is_above_2_percent === false || item.is_above_2_percent === 'No' ? 'selected' : ''}>No</option>
                    <option style="background: #1e1e1e; color: #fff;" value="Yes" ${item.is_above_2_percent === true || item.is_above_2_percent === 'Yes' ? 'selected' : ''}>Yes</option>
                </select>
                ${manualAsterisk}
            </div>
        </td>`;

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

        let isOverridden = !!item._edited_expected_amount;
        let expectedAmountHTML = item._edited_expected_amount || (item.expected_amount ? `${parseFloat(item.expected_amount).toFixed(2)} <span style="font-size: 0.8em; color: #aaa;">(${item.expected_type || 'Interim'})</span>` : '-');

        // Always strip existing asterisk marks before rendering to avoid duplicates when manually edited
        expectedAmountHTML = expectedAmountHTML.replace(/<span[^>]*class=["']asterisk-mark["'][^>]*>\*<\/span>/gi, '').replace(/\*/g, '');

        let bmDateHtml = '-';
        if (item.board_meeting_date) {
            let parts = item.board_meeting_date.split('T');
            let dateStr = parts[0].split('-').reverse().join('-');
            if (parts.length > 1 && parts[1] && parts[1] !== '00:00:00') {
                bmDateHtml = `${dateStr}<br><span style="font-size: 0.85em; color: #aaa;">${parts[1].split('.')[0]}</span>`;
            } else {
                bmDateHtml = dateStr;
            }
        }

        let broadcastDateHtml = '-';
        if (item.broadcast_date) {
            let parts = item.broadcast_date.split('T');
            let dateStr = parts[0].split('-').reverse().join('-');
            if (parts.length > 1 && parts[1] && parts[1] !== '00:00:00') {
                broadcastDateHtml = `${dateStr}<br><span style="font-size: 0.85em; color: #aaa;">${parts[1].split('.')[0]}</span>`;
            } else {
                broadcastDateHtml = dateStr;
            }
        }

        if (isOverridden) {
            expectedAmountHTML = `${expectedAmountHTML} <span class="asterisk-mark" style="color: #ffeb3b; font-size: 1.2em; font-weight: bold; margin-left: 4px;" title="Manually Edited">*</span>`;
        } else if (item.expected_highly_likely && typeof item.expected_highly_likely === 'string' && item.expected_highly_likely.includes('Announced:')) {
            // If it's already officially announced, we strictly show the announced value without trend arrows
            // Just use the base expectedAmountHTML which is the announced value.
        } else if (item.expected_amount && item.expected_amount_compare) {
            let numExpected = parseFloat(item.expected_amount);
            let numLast = parseFloat(item.expected_amount_compare);
            if (numExpected > numLast) {
                expectedAmountHTML = `${expectedAmountHTML} <span style="color: #60a5fa; margin-left: 5px;">&#8593;</span>`; // Up arrow blue
            } else if (numExpected < numLast) {
                expectedAmountHTML = `${expectedAmountHTML} <span style="color: #ff4d4d; margin-left: 5px;">&#8595;</span>`; // Down arrow red
            }
        }

        let expectedHighlyLikelyHtml = item.expected_highly_likely || '-';

        let lastFaceValueHtml = (item.last_face_value !== undefined && item.last_face_value !== null) ? item.last_face_value : '-';
        let lastPurposeHtml = (item.last_purpose) ? item.last_purpose : '-';
        let lastAgmDateHtml = item.last_agm_date || '-';
        let lastAgmAnnHtml = item.last_agm_announcement_date || '-';

        html += `
            <tr style="cursor: pointer; border-bottom: 2px solid #222;" onclick="toggleSSDivHistory('${item.symbol}')">
                <td style="font-weight: bold; color: #fff;">
                    <span style="margin-right: 5px; color: #888; font-size: 10px; display: inline-block; width: 12px;" id="caret-${item.symbol}">&#9654;</span>${item.symbol}
                </td>
                <td>${item.sector || '-'}</td>
                <td>${item.lot_size || '-'}</td>
                <td>${item.spot ? item.spot.toFixed(2) : '-'}</td>
                ${futuresHTML}
                <td style="background: rgba(43, 58, 74, 0.4);">${item.last_type || '-'}</td>
                <td style="background: rgba(43, 58, 74, 0.4);">${lastExDateHtml}</td>
                <td style="background: rgba(43, 58, 74, 0.4);">${bmDateHtml}</td>
                <td style="background: rgba(43, 58, 74, 0.4);">${lastFaceValueHtml}</td>
                <td style="background: rgba(43, 58, 74, 0.4);">${lastPurposeHtml}</td>
                <td style="background: rgba(43, 58, 74, 0.4); font-weight: bold;">${lastAmountHtml}</td>
                <td style="background: rgba(43, 58, 74, 0.4);">${lastAgmDateHtml}</td>
                <td style="background: rgba(43, 58, 74, 0.4);">${lastAgmAnnHtml}</td>
                <td style="background: rgba(26, 26, 26, 0.6); color: #bbb; text-align: center;">${bmDateHtml}</td>
                <td style="background: rgba(26, 26, 26, 0.6); color: #bbb; text-align: center;">${broadcastDateHtml}</td>
                ${above2Cell}
                <td style="background: rgba(51, 77, 61, 0.4); color: #8fbc8f; font-weight: bold;" contenteditable="true" onblur="updateSSDivData('${item.symbol}', 'expected_amount', this.innerHTML)" onclick="event.stopPropagation();">${expectedAmountHTML}</td>
                <td style="background: rgba(51, 77, 61, 0.4); color: #8fbc8f; font-weight: bold;" contenteditable="true" onblur="updateSSDivData('${item.symbol}', 'expected_highly_likely', this.innerText)" onclick="event.stopPropagation();">${expectedHighlyLikelyHtml}</td>
                <td style="background: rgba(107, 96, 33, 0.4); color: #ffd700;" contenteditable="true" onblur="updateSSDivData('${item.symbol}', 'expected_less_likely', this.innerText)" onclick="event.stopPropagation();">${item.expected_less_likely || '-'}</td>
                <td style="background: rgba(43, 58, 74, 0.4);" contenteditable="true" onblur="updateSSDivData('${item.symbol}', 'note', this.innerText)" onclick="event.stopPropagation();">${item.note || '-'}</td>
                <td><button class="btn btn-secondary" style="font-size: 11px;" onclick="event.stopPropagation(); if (typeof switchClientTab === 'function') { switchClientTab('ai'); } else { switchMainTab('ai_analyze'); } setTimeout(() => { const input = document.getElementById('chat-input') || document.getElementById('ai-cmd-input'); if(input) { input.value = 'dividend analysis: ${item.symbol}, find out the latest expected dividend and expected date'; input.focus(); } }, 500)"><i class="fas fa-robot"></i> AI Analyze</button></td>
            </tr>
        `;

        if (item.history && item.history.length > 0) {
            let histRows = '';
            window._prevFy = undefined;
            item.history.forEach(h => {
                // We don't make history editable, only the main row. But to be consistent:
                const histAbove2 = h.is_above_2_percent ? `<td style="color: #ff4d4d; font-weight: bold;">Yes</td>` : `<td>No</td>`;

                let annDateHtml = '-';
                // In Special Sit Historical, we use announcement_date_obj which we have mapped strictly
                // to the Board Meeting's Exact Declaration Timestamp.
                let baseAnnDate = h.announcement_date_obj || h.broadcast_date;
                if (baseAnnDate) {
                    let parts = baseAnnDate.split('T');
                    let d = parts[0];
                    if (parts.length > 1 && parts[1] && parts[1] !== '00:00:00') {
                        annDateHtml = `${d} <span style="color:#aaa; font-size:0.85em;">${parts[1].split('.')[0]}</span>`;
                    } else {
                        annDateHtml = d;
                    }
                }


                // Track FY borders
                let fyBorder = '';
                if (window._prevFy !== undefined && window._prevFy !== h.fy_year) {
                    // Add a distinct separator row instead of just a thick border
                    histRows += `
                    <tr style="background: #2a2a2a;">
                        <td colspan="14" style="text-align: center; font-size: 0.85em; color: #888; padding: 2px 0; border-top: 2px solid #555; border-bottom: 2px solid #555;">
                            --- End of Financial Year ---
                        </td>
                    </tr>`;
                }
                window._prevFy = h.fy_year;

                let dpsHtml = h.amount !== null && h.amount !== undefined ? parseFloat(h.amount).toFixed(2) : '-';
                let epsHtml = h.eps !== null && h.eps !== undefined ? parseFloat(h.eps).toFixed(2) : '-';
                let npHtml = h.net_profit !== null && h.net_profit !== undefined ? parseFloat(h.net_profit).toFixed(2) : '-';
                let payoutHtml = h.payout_ratio !== null && h.payout_ratio !== undefined ? parseFloat(h.payout_ratio).toFixed(1) + '%' : '-';
                let yieldHtml = h.dividend_yield !== null && h.dividend_yield !== undefined ? parseFloat(h.dividend_yield).toFixed(2) + '%' : '-';

                let deltaDpsColor = h.delta_dps_pct > 0 ? '#4caf50' : (h.delta_dps_pct < 0 ? '#f44336' : '#aaa');
                let deltaDpsHtml = h.delta_dps_pct !== null && h.delta_dps_pct !== undefined ? `<span style="color:${deltaDpsColor}">${h.delta_dps_pct}%</span>` : '-';

                let deltaEpsColor = h.delta_eps_pct > 0 ? '#4caf50' : (h.delta_eps_pct < 0 ? '#f44336' : '#aaa');
                let deltaEpsHtml = h.delta_eps_pct !== null && h.delta_eps_pct !== undefined ? `<span style="color:${deltaEpsColor}">${h.delta_eps_pct}%</span>` : '-';

                let fyTotalHtml = h.fy_total_dps !== null && h.fy_total_dps !== undefined ? parseFloat(h.fy_total_dps).toFixed(2) : '-';

                let agmAnnDate = h.agm_announcement_date || '-';
                let agmDate = h.agm_date || '-';

                histRows += `
                    <tr>
                        <td>${h.ex_date || '-'}</td>
                        <td>${h.dividend_type || '-'}</td>
                        <td>${h.face_value !== undefined && h.face_value !== null ? h.face_value : '-'}</td>
                        <td style="max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${h.purpose || '-'}">${h.purpose || '-'}</td>
                        <td style="font-weight: bold; color: #60a5fa;">${dpsHtml}</td>
                        <td style="color: #ffd700;">${epsHtml}</td>
                        <td style="color: #ff9800;">${npHtml}</td>
                        <td style="color: #bbb;">${payoutHtml}</td>
                        <td style="color: #8fbc8f;">${yieldHtml}</td>
                        <td>${deltaDpsHtml}</td>
                        <td>${deltaEpsHtml}</td>
                        <td style="font-weight: bold; color: #fff;">${fyTotalHtml} <small style="color:#666;">(FY${h.fy_year})</small></td>
                        <td>${agmAnnDate}</td>
                        <td>${agmDate}</td>
                        ${histAbove2}
                    </tr>
                `;
            });

            html += `
            <tr id="ss-div-hist-${item.symbol}" style="display: none; background: #1a1a1a;">
                <td colspan="18" style="padding: 15px;">
                    <div style="border-left: 3px solid #3176B8; padding-left: 15px; margin-left: 20px;">
                        <h4 style="margin: 0 0 10px 0; color: #ccc;">Historical Dividends (Last 10 Years)</h4>
                        <table class="data-table" style="width: 95%; min-width: 800px; background: #222; border-collapse: separate; border-spacing: 0;">
                            <thead>
                                <tr>
                                    <th>Ex-Date</th>
                                    <th>Type</th>
                                    <th>Face Value</th>
                                    <th>Purpose</th>
                                    <th>DPS</th>
                                    <th>EPS</th>
                                    <th>Net Profit</th>
                                    <th>Payout %</th>
                                    <th>Yield %</th>
                                    <th>Δ DPS %</th>
                                    <th>Δ EPS %</th>
                                    <th>FY Total</th>
                                    <th>AGM Announce</th>
                                    <th>AGM Date</th>
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

    if (html === '') {
        html = '<tr><td colspan="18" style="text-align:center;">No data available for selected criteria</td></tr>';
    }

    tbody.innerHTML = html;
}

// --- OFS Bid Matrix Logic ---
function initializeOFSMatrix() {
    const tbody = document.getElementById('ofs-matrix-body');
    if (tbody && tbody.children.length === 0) {
        // Add 3 empty rows by default
        addOFSMatrixRow(true);
        addOFSMatrixRow(true);
        addOFSMatrixRow(true);
    }
}

function addOFSMatrixRow(isInit = false) {
    const tbody = document.getElementById('ofs-matrix-body');
    if (!tbody) return;

    const tr = document.createElement('tr');
    tr.style.textAlign = 'right';
    tr.innerHTML = `
        <td style="text-align: left; padding: 4px; border: 1px solid #444;">
            <input type="text" class="ofs-matrix-price history-input" style="width: 80px;" oninput="calculateOFS()">
        </td>
        <td style="padding: 4px; border: 1px solid #444;">
            <input type="number" class="ofs-matrix-qty history-input" style="width: 100px;" oninput="calculateOFS()">
        </td>
        <td style="padding: 4px; border: 1px solid #444;">
            <input type="number" class="ofs-matrix-cumul history-input" style="width: 100px;" oninput="calculateOFS()">
        </td>
        <td class="ofs-matrix-supply" style="padding: 4px; border: 1px solid #444; color: #ccc;">0</td>
        <td class="ofs-matrix-allot-pct" style="padding: 4px; border: 1px solid #444; color: #888;">0.00%</td>
        <td class="ofs-matrix-allot-shares" style="padding: 4px; border: 1px solid #444; color: #ccc;">0</td>
    `;
    tbody.appendChild(tr);
    if (!isInit) calculateOFS();
}

function removeOFSMatrixRow() {
    const tbody = document.getElementById('ofs-matrix-body');
    if (!tbody || tbody.children.length === 0) return;
    tbody.removeChild(tbody.lastChild);
    calculateOFS();
}

// Hook into tab selection to initialize the matrix
document.addEventListener('DOMContentLoaded', () => {
    // Wait for the elements to be present or initialize directly
    initializeOFSMatrix();
});
