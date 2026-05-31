let _putCallParityRawData = null;

async function loadPutCallParity() {
    try {
        const selectedExpiry = document.getElementById('putcall-expiry-select').value;
        const atmFilterOnly = document.getElementById('putcall-atm-filter').checked;

        let data = _putCallParityRawData;
        if (!data) {
            const res = await fetch('/api/data/derivatives/put_call_parity?symbol=NIFTY');
            data = await res.json();
            _putCallParityRawData = data;
        }

        if (!data || !data.data || data.data.length === 0) {
            document.getElementById('putcall-parity-body').innerHTML = '<tr><td colspan="13" style="text-align: center; color: #888;">No data found.</td></tr>';
            return;
        }

        const futures = data.futures;
        const allExpiries = [...new Set(data.data.map(d => d.expiry))].sort((a, b) => new Date(a) - new Date(b));

        // Update Expiry Select Dropdown
        const selectEl = document.getElementById('putcall-expiry-select');
        if (selectEl.options.length <= 1) { // Only 'ALL' is there
            selectEl.innerHTML = '<option value="ALL">All Expiries</option>';
            allExpiries.forEach(exp => {
                selectEl.innerHTML += `<option value="${exp}">${exp}</option>`;
            });
        }

        // Map weekly option expiries to their respective monthly future
        // A monthly future usually expires on the last Thursday.
        // For any weekly expiry, the respective monthly future is the smallest future expiry >= the weekly expiry.
        // Or if none is >=, it's the largest future expiry (edge case).
        const futureExpiries = Object.keys(futures).sort((a, b) => new Date(a) - new Date(b));
        const getMonthlyFuture = (optExpiry) => {
            const optDate = new Date(optExpiry);
            for (let futExp of futureExpiries) {
                if (new Date(futExp) >= optDate) {
                    return { date: futExp, price: futures[futExp] };
                }
            }
            if (futureExpiries.length > 0) {
                const last = futureExpiries[futureExpiries.length - 1];
                return { date: last, price: futures[last] };
            }
            return { date: "-", price: 0.0 };
        };

        // Filter and calculate
        let displayData = data.data;
        if (selectedExpiry !== 'ALL') {
            displayData = displayData.filter(d => d.expiry === selectedExpiry);
        }

        // Sort by expiry, then strike
        displayData.sort((a, b) => {
            if (a.expiry !== b.expiry) return new Date(a.expiry) - new Date(b.expiry);
            return a.strike - b.strike;
        });

        let html = '';
        displayData.forEach(row => {
            const monthlyFut = getMonthlyFuture(row.expiry);

            // Filter Near ATM (+/- 500 points)
            if (atmFilterOnly) {
                if (Math.abs(row.strike - monthlyFut.price) > 500) {
                    return; // Skip this row
                }
            }

            // Synthetic Future = Strike + Call LTP - Put LTP
            const synthFuture = row.strike + row.ce_ltp - row.pe_ltp;
            const diff = synthFuture - monthlyFut.price;

            // ATM highlighting: If strike is within 50 points of the Nifty Future
            const isATM = Math.abs(row.strike - monthlyFut.price) <= 50;
            const rowStyle = isATM ? 'background: rgba(96, 165, 250, 0.1);' : '';

            const diffColor = diff > 0 ? '#60a5fa' : (diff < 0 ? '#ff4d4d' : '#fff');

            html += `<tr style="${rowStyle}">
                <td>${row.expiry}</td>
                <td>${row.dte}</td>
                <td>${row.strike}</td>
                <td>${row.ce_ltp.toFixed(2)}</td>
                <td>${row.pe_ltp.toFixed(2)}</td>
                <td style="color: #ff9800; font-weight: bold;">${synthFuture.toFixed(2)}</td>
                <td style="color: #60a5fa;">${monthlyFut.price.toFixed(2)} (${monthlyFut.date})</td>
                <td style="color: ${diffColor}; font-weight: bold;">${diff.toFixed(2)}</td>
                <td>${row.ce_vol.toLocaleString()}</td>
                <td>${row.ce_oi.toLocaleString()}</td>
                <td>${row.pe_vol.toLocaleString()}</td>
                <td>${row.pe_oi.toLocaleString()}</td>
                <td>${row.timestamp}</td>
            </tr>`;
        });

        document.getElementById('putcall-parity-body').innerHTML = html;

    } catch (e) {
        console.error("Error loading Put-Call Parity", e);
        document.getElementById('putcall-parity-body').innerHTML = `<tr><td colspan="13" style="text-align: center; color: #ff4d4d;">Failed to load data: ${e.message}</td></tr>`;
    }
}

function exportPutCallParity() {
    if (typeof exportTableToCSV === 'function') {
        exportTableToCSV('putcall-parity-table', 'Put_Call_Parity_Nifty.csv');
    } else {
        alert("Export function not available.");
    }
}
