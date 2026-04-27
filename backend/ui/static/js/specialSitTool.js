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

function calculateBuyback() {
    const promoter = parseFloat(document.getElementById('bb-promoter').value) || 0;
    const fii = parseFloat(document.getElementById('bb-fii').value) || 0;
    const dii = parseFloat(document.getElementById('bb-dii').value) || 0;
    const retail = parseFloat(document.getElementById('bb-retail').value) || 0;
    const publicVal = parseFloat(document.getElementById('bb-public').value) || 0;

    const totalOut = promoter + fii + dii + retail + publicVal;
    document.getElementById('bb-total-out').innerText = totalOut.toLocaleString();

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

    // Calculate Arbitrage Scenario (Mock Logic as detailed formulas were omitted)
    const eqProfit = sharesCalc * (buybackPrice - cmp);
    const futLoss = sharesCalc * (cmp - futPrice);
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

    // Participation Table mock values based on shares (Assuming acceptance ratios)
    const accNon100 = pubOffer / ((totalOut - retail) || 1) * 100;
    const accRet100 = resRetailOffer / (retail || 1) * 100;

    document.getElementById('bb-acc-non-100').innerText = accNon100.toFixed(2) + '%';
    document.getElementById('bb-acc-non-90').innerText = (accNon100 * 1.1).toFixed(2) + '%';
    document.getElementById('bb-acc-non-80').innerText = (accNon100 * 1.2).toFixed(2) + '%';

    document.getElementById('bb-acc-ret-100').innerText = accRet100.toFixed(2) + '%';
    document.getElementById('bb-acc-ret-90').innerText = (accRet100 * 1.1).toFixed(2) + '%';
    document.getElementById('bb-acc-ret-80').innerText = (accRet100 * 1.2).toFixed(2) + '%';
}

async function syncBuybackHoldings() {
    const symbol = document.getElementById('bb-symbol').value.toUpperCase();
    if (!symbol) {
        alert("Please enter a symbol in Price Info to sync holdings.");
        return;
    }

    try {
        const res = await fetch(`/api/data/fundamentals/${symbol}`);
        const data = await res.json();

        if (data.total_outstanding) {
            document.getElementById('bb-promoter').value = data.promoter_holding || 0;
            document.getElementById('bb-fii').value = data.fii_holding || 0;
            document.getElementById('bb-dii').value = data.dii_holding || 0;
            document.getElementById('bb-public').value = data.public_holding || 0;

            // Re-trigger calculation
            calculateBuyback();
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
        // Using snapshot endpoint to get latest cash and future price
        const ts = new Date().toISOString().split('T')[0];
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
