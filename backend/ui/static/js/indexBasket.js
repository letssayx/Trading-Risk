let basketData = [];
let basketHistory = []; // For Undo functionality

function downloadIdxBasketTemplate() {
    const csvContent = "Symbol,Weight,Lot Size\nRELIANCE,10.50,250\nHDFCBANK,9.20,550\nINFY,6.10,400\n";
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "Nifty_Basket_Template.csv");
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function handleIdxBasketUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        parseIdxBasketCSV(text);
        // Reset file input so same file can be uploaded again if needed
        event.target.value = '';
    };
    reader.readAsText(file);
}

function parseIdxBasketCSV(csvText) {
    const lines = csvText.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    if (lines.length < 2) {
        alert("Invalid CSV format. Need headers and at least one row.");
        return;
    }

    // Skip header
    const newBasket = [];
    for (let i = 1; i < lines.length; i++) {
        const parts = lines[i].split(',').map(p => p.trim());
        if (parts.length >= 2) {
            newBasket.push({
                symbol: parts[0].toUpperCase(),
                weight: parseFloat(parts[1]) || 0.0,
                lotSize: parts.length > 2 ? parseInt(parts[2]) : 1, // Default to 1 if lot size not provided
                price: 0.0,
                shares: 0,
                lotsToTrade: 0,
                expiry: '-',
                vol: 0,
                oi: 0,
                timestamp: '-'
            });
        }
    }

    if (newBasket.length > 0) {
        saveState();
        basketData = newBasket;
        loadIdxBasketData();
    }
}

async function loadIdxBasketData() {
    if (basketData.length === 0) {
        document.getElementById('idxbasket-body').innerHTML = '<tr><td colspan="11" style="text-align: center; color: #888;">No symbols in basket. Upload CSV or Add manually.</td></tr>';
        return;
    }

    try {
        const expiryType = document.getElementById('idxbasket-expiry-select').value;
        const symbols = basketData.map(b => b.symbol);

        // Fetch prices from backend
        const res = await fetch(`/api/data/derivatives/index_basket_data?expiry_type=${expiryType}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(symbols)
        });

        const respData = await res.json();
        if (!respData || !respData.data) {
            throw new Error("Invalid response from server");
        }

        const priceData = respData.data;
        const niftyData = respData.nifty;

        // Update basket data with prices
        let totalWeight = 0;
        basketData.forEach(item => {
            const fd = priceData[item.symbol];
            if (fd) {
                item.price = fd.price;
                item.expiry = fd.expiry;
                item.vol = fd.vol;
                item.oi = fd.oi;
                item.timestamp = fd.timestamp;
            }
            totalWeight += item.weight;
        });

        // 1. Calculate Minimum Multiplier
        // We need: (Multiplier * Weight / 100) >= Lot Size
        // => Multiplier >= (Lot Size * 100) / Weight
        let minMultiplier = 0;
        basketData.forEach(item => {
            if (item.weight > 0) {
                const reqM = (item.lotSize * 100) / item.weight;
                if (reqM > minMultiplier) {
                    minMultiplier = reqM;
                }
            }
        });

        // Round multiplier up to nearest reasonable unit (e.g. integer)
        minMultiplier = Math.ceil(minMultiplier);

        // 2. Calculate Shares, Lots, and Basket Value
        let totalBasketValue = 0;
        let totalActualBasketValue = 0; // Value based on actual lots traded

        basketData.forEach(item => {
            if (item.weight > 0 && item.price > 0) {
                // Theoretical shares based on multiplier
                item.shares = (minMultiplier * (item.weight / 100));

                // Actual lots to trade (must be integer)
                item.lotsToTrade = Math.round(item.shares / item.lotSize);

                const theoreticalValue = item.shares * item.price;
                const actualValue = item.lotsToTrade * item.lotSize * item.price;

                totalBasketValue += theoreticalValue;
                totalActualBasketValue += actualValue;
            }
        });

        // For Nifty comparison, index value vs basket value requires divisor logic.
        // Assuming minMultiplier is total index value, theoretical basket value is just index tracking.
        // However, a simple comparison is the weighted sum.
        // Let's normalize Basket Value to an Index point equivalent.
        // If sum(Weight) = 100, then (totalBasketValue / minMultiplier) should equal Nifty price roughly.

        const normalizedBasketPts = minMultiplier > 0 ? (totalBasketValue / minMultiplier) : 0;
        const targetNiftyFut = niftyData ? niftyData.price : 0.0;
        const diffBasisPts = targetNiftyFut > 0 ? ((normalizedBasketPts - targetNiftyFut) / targetNiftyFut) * 10000 : 0;

        // Tracking error due to round lots
        const basketErrorValue = totalActualBasketValue - totalBasketValue;
        const basketErrorPct = totalBasketValue > 0 ? (basketErrorValue / totalBasketValue) * 100 : 0;

        // Render Summary
        document.getElementById('idxbasket-val').innerText = normalizedBasketPts.toFixed(2);
        document.getElementById('idxbasket-nifty-fut').innerText = targetNiftyFut > 0 ? targetNiftyFut.toFixed(2) : '-';

        const diffEl = document.getElementById('idxbasket-diff');
        diffEl.innerText = diffBasisPts.toFixed(2) + ' bps';
        diffEl.style.color = diffBasisPts > 0 ? '#60a5fa' : (diffBasisPts < 0 ? '#ff4d4d' : '#ff9800');

        document.getElementById('idxbasket-multiplier').innerText = `${minMultiplier.toLocaleString()} / ${basketErrorPct.toFixed(3)}%`;

        renderIdxBasketTable();

    } catch (e) {
        console.error("Error calculating basket", e);
        document.getElementById('idxbasket-body').innerHTML = `<tr><td colspan="11" style="text-align: center; color: #ff4d4d;">Failed to calculate: ${e.message}</td></tr>`;
    }
}

function renderIdxBasketTable() {
    const tbody = document.getElementById('idxbasket-body');
    let html = '';

    basketData.forEach((item, index) => {
        html += `<tr>
            <td style="text-align: center;">
                <button class="btn btn-secondary" style="padding: 2px 5px;" onclick="removeIdxBasketRow(${index})"><i class="fas fa-trash" style="color: #ff4d4d;"></i></button>
            </td>
            <td style="font-weight: bold;">${item.symbol}</td>
            <td contenteditable="true" class="editable-cell" onblur="updateIdxBasketCell(${index}, 'weight', this.innerText)">${item.weight.toFixed(2)}</td>
            <td style="color: #60a5fa;">${item.price.toFixed(2)}</td>
            <td contenteditable="true" class="editable-cell" onblur="updateIdxBasketCell(${index}, 'lotSize', this.innerText)">${item.lotSize}</td>
            <td>${item.shares.toFixed(2)}</td>
            <td style="color: #ff9800; font-weight: bold;">${item.lotsToTrade}</td>
            <td>${item.expiry}</td>
            <td>${item.vol.toLocaleString()}</td>
            <td>${item.oi.toLocaleString()}</td>
            <td>${item.timestamp}</td>
        </tr>`;
    });

    tbody.innerHTML = html;

    // Add styles for editable cells dynamically if not in CSS
    const styleId = 'idxbasket-styles';
    if (!document.getElementById(styleId)) {
        const style = document.createElement('style');
        style.id = styleId;
        style.innerHTML = `
            .editable-cell { cursor: text; transition: background 0.2s; }
            .editable-cell:hover { background: rgba(255,255,255,0.1); }
            .editable-cell:focus { outline: 1px solid #60a5fa; background: rgba(0,0,0,0.5); }
        `;
        document.head.appendChild(style);
    }
}

function updateIdxBasketCell(index, field, value) {
    let numVal = parseFloat(value);
    if (isNaN(numVal) || numVal < 0) {
        alert("Invalid number");
        renderIdxBasketTable(); // Revert UI
        return;
    }

    if (basketData[index][field] !== numVal) {
        saveState();
        basketData[index][field] = numVal;
        loadIdxBasketData(); // Recalculate everything
    }
}

function addIdxBasketRow() {
    const sym = prompt("Enter Symbol:");
    if (!sym) return;

    saveState();
    basketData.push({
        symbol: sym.toUpperCase(),
        weight: 0.0,
        lotSize: 1,
        price: 0.0,
        shares: 0,
        lotsToTrade: 0,
        expiry: '-',
        vol: 0,
        oi: 0,
        timestamp: '-'
    });

    // Automatically trigger a fetch for the new symbol's price
    loadIdxBasketData();
}

function removeIdxBasketRow(index) {
    saveState();
    basketData.splice(index, 1);
    loadIdxBasketData();
}

function saveState() {
    // Deep copy current state into history
    basketHistory.push(JSON.parse(JSON.stringify(basketData)));
    if (basketHistory.length > 20) {
        basketHistory.shift(); // Keep last 20 states
    }
}

function revertIdxBasket() {
    if (basketHistory.length > 0) {
        basketData = basketHistory.pop();
        loadIdxBasketData();
    } else {
        alert("No more actions to undo.");
    }
}

function exportIdxBasket() {
    if (typeof exportTableToCSV === 'function') {
        exportTableToCSV('idxbasket-table', 'Index_Basket_Nifty.csv');
    } else {
        alert("Export function not available.");
    }
}
