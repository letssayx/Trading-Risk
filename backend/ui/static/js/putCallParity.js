let _putCallParityRawData = null;

async function loadPutCallParity(forceRefresh = false) {
    try {
        const selectedExpiry = document.getElementById('putcall-expiry-select').value;
        const selectedStrike = document.getElementById('putcall-strike-select').value;
        const atmFilterOnly = document.getElementById('putcall-atm-filter').checked;

        if (forceRefresh) _putCallParityRawData = null;

        let data = _putCallParityRawData;
        if (!data) {
            const res = await fetch('/api/data/derivatives/put_call_parity?symbol=NIFTY');
            data = await res.json();
            _putCallParityRawData = data;
        }

        if (!data || !data.data || data.data.length === 0) {
            document.getElementById('putcall-parity-body').innerHTML = '<tr><td colspan="18" style="text-align: center; color: #888;">No data found.</td></tr>';
            return;
        }

        const futures = data.futures;
        const pastDates = data.past_dates || [];
        const allExpiries = [...new Set(data.data.map(d => d.expiry))].sort((a, b) => new Date(a) - new Date(b));

        // Update Table Headers for Past Dates
        for (let i = 0; i < 5; i++) {
            const th = document.getElementById(`th-diff-t${i+1}`);
            if (th) {
                th.innerText = pastDates[i] || `T-${i+1} Diff`;
            }
        }

        // Update Expiry Select Dropdown
        const selectEl = document.getElementById('putcall-expiry-select');
        if (selectEl.options.length <= 1) { // Only 'ALL' is there
            selectEl.innerHTML = '<option value="ALL">All Expiries</option>';
            allExpiries.forEach(exp => {
                selectEl.innerHTML += `<option value="${exp}">${exp}</option>`;
            });
        }

        // Update Strike Select Dropdown
        const allStrikes = [...new Set(data.data.map(d => d.strike))].sort((a, b) => a - b);
        const strikeSelectEl = document.getElementById('putcall-strike-select');
        if (strikeSelectEl.options.length <= 1) {
            strikeSelectEl.innerHTML = '<option value="ALL">All Strikes</option>';
            allStrikes.forEach(strike => {
                strikeSelectEl.innerHTML += `<option value="${strike}">${strike}</option>`;
            });
        }

        // Map weekly option expiries to their respective monthly future
        // A monthly future usually expires on the last Thursday.
        // For any weekly expiry, the respective monthly future is the smallest future expiry >= the weekly expiry.
        // Or if none is >=, it's the largest future expiry (edge case).
                const getMonthlyFuture = (optExpiry, targetTradeDate) => {
            if (!optExpiry) return { date: "-", price: 0.0, vol: 0 };
            const futsForDate = futures[targetTradeDate] || {};
            const futureExpiries = Object.keys(futsForDate).sort((a, b) => new Date(a) - new Date(b));

            const optDate = new Date(optExpiry);
            const optMonth = optDate.getMonth();
            const optYear = optDate.getFullYear();

            // Priority 1: Match exactly the same month and year
            for (let futExp of futureExpiries) {
                const fDate = new Date(futExp);
                if (fDate.getMonth() === optMonth && fDate.getFullYear() === optYear) {
                    return { date: futExp, price: futsForDate[futExp].price, vol: futsForDate[futExp].vol };
                }
            }

            // Priority 2: Fallback to next available future
            for (let futExp of futureExpiries) {
                if (new Date(futExp) >= optDate) {
                    return { date: futExp, price: futsForDate[futExp].price, vol: futsForDate[futExp].vol };
                }
            }
            if (futureExpiries.length > 0) {
                const last = futureExpiries[futureExpiries.length - 1];
                return { date: last, price: futsForDate[last].price, vol: futsForDate[last].vol };
            }
            return { date: "-", price: 0.0, vol: 0 };
        };

        // Filter and calculate
        let displayData = data.data;
        const currentTradeDate = data.date;

        // Update Header
        if (data.date) {
            document.getElementById('pcp-report-date').innerText = `Bhavcopy Date: ${data.date}`;
        }
        if (data.spot_price !== undefined) {
            document.getElementById('pcp-spot-price').innerText = `Spot: ${data.spot_price > 0 ? data.spot_price.toFixed(2) : 'N/A'}`;
        }

        let targetFuturePrice = 0.0;
        if (selectedExpiry !== 'ALL') {
            const monthlyFut = getMonthlyFuture(selectedExpiry, currentTradeDate);
            targetFuturePrice = monthlyFut.price;
        } else {
            if (futures[currentTradeDate]) {
                const futExpiries = Object.keys(futures[currentTradeDate]).sort((a, b) => new Date(a) - new Date(b));
                if (futExpiries.length > 0) {
                    targetFuturePrice = futures[currentTradeDate][futExpiries[0]].price;
                }
            }
        }
        document.getElementById('pcp-future-price').innerText = `Future: ${targetFuturePrice > 0 ? targetFuturePrice.toFixed(2) : 'N/A'}`;

        if (selectedExpiry !== 'ALL') {
            displayData = displayData.filter(d => d.expiry === selectedExpiry);
        }
        if (selectedStrike !== 'ALL') {
            const strikeVal = parseFloat(selectedStrike);
            displayData = displayData.filter(d => d.strike === strikeVal);
        }

        // Sort by expiry, then strike
        displayData.sort((a, b) => {
            if (a.expiry !== b.expiry) return new Date(a.expiry) - new Date(b.expiry);
            return a.strike - b.strike;
        });

        let html = '';
        displayData.forEach(row => {
            const monthlyFut = getMonthlyFuture(row.expiry, currentTradeDate);

            // Filter Near ATM (+/- 500 points)
            if (atmFilterOnly) {
                if (Math.abs(row.strike - monthlyFut.price) > 500) {
                    return; // Skip this row
                }
            }

            // Synthetic Future = Strike + Call LTP - Put LTP
            const synthFuture = row.strike + row.ce_ltp - row.pe_ltp;
            const diff = synthFuture - monthlyFut.price;

            // Calculate Historical Diffs
            let histDiffHtml = '';
            for (let i = 0; i < 5; i++) {
                const pd = pastDates[i];
                if (pd && row.history && row.history[pd]) {
                    const histData = row.history[pd];
                    if (histData.ce > 0 || histData.pe > 0) {
                        const histSynth = row.strike + histData.ce - histData.pe;
                        const histMonthlyFut = getMonthlyFuture(row.expiry, pd);
                        if (histMonthlyFut.price > 0) {
                            const histDiff = histSynth - histMonthlyFut.price;
                            const hColor = histDiff > 0 ? '#60a5fa' : (histDiff < 0 ? '#ff4d4d' : '#fff');
                            histDiffHtml += `<td style="color: ${hColor};">${histDiff.toFixed(2)}</td>`;
                        } else {
                            histDiffHtml += `<td style="color: #555;">-</td>`;
                        }
                    } else {
                        histDiffHtml += `<td style="color: #555;">-</td>`;
                    }
                } else {
                    histDiffHtml += `<td style="color: #555;">-</td>`;
                }
            }

            // ATM highlighting: If strike is within 50 points of the Nifty Future
            const isATM = Math.abs(row.strike - monthlyFut.price) <= 50;
            const rowStyle = isATM ? 'background: rgba(96, 165, 250, 0.1);' : '';

            const diffColor = diff > 0 ? '#60a5fa' : (diff < 0 ? '#ff4d4d' : '#fff');

            html += `<tr style="${rowStyle}">
                <td style="text-align: center;">${row.expiry}</td>
                <td style="text-align: center;">${row.dte}</td>
                <td>${row.strike}</td>
                <td>${row.ce_ltp.toFixed(2)}</td>
                <td>${row.pe_ltp.toFixed(2)}</td>
                <td style="color: #ff9800; font-weight: bold;">${synthFuture.toFixed(2)}</td>
                <td style="color: #60a5fa;">${monthlyFut.price.toFixed(2)} (${monthlyFut.date})</td>
                <td style="color: ${diffColor}; font-weight: bold;">${diff.toFixed(2)}</td>
                ${histDiffHtml}
                                <td>${row.ce_vol.toLocaleString()}</td>
                <td>${row.ce_oi.toLocaleString()}</td>
                <td>${row.pe_vol.toLocaleString()}</td>
                <td>${row.pe_oi.toLocaleString()}</td>
                <td style="text-align: center; color: #888;">${row.timestamp}</td>
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
