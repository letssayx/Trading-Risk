async function loadMWPLAnalysis(isRefresh = false) {
    const thead = document.querySelector('#mwpl-analysis-table thead');
    const tbody = document.getElementById('mwpl-analysis-body');
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#888;">Loading...</td></tr>';

    const loadBtn = document.getElementById('btn-load-mwpl');
    let originalText = '';
    if (loadBtn) {
        originalText = loadBtn.innerHTML;
        loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        loadBtn.disabled = true;
    }

    let selectedDays = 14;
    const radios = document.getElementsByName('mwpl_days');
    for (let i = 0; i < radios.length; i++) {
        if (radios[i].checked) {
            selectedDays = parseInt(radios[i].value);
            break;
        }
    }

    try {
        if (isRefresh) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#888;">Checking for new data and syncing...</td></tr>';
            const force = document.getElementById('mwpl-force-refresh') && document.getElementById('mwpl-force-refresh').checked;
            await fetch(`/api/data/analysis/mwpl/sync?force=${force}`, { method: 'POST' });
        }
        const res = await fetch(`/api/data/derivatives/mwpl_historical?days=${selectedDays}`);
        const result = await res.json();

        if (!res.ok || result.status !== "success") {
            throw new Error(result.detail || "Failed to load MWPL history");
        }

        const data = result.data;

        tbody.innerHTML = '';

        // Clean up old dynamically created tbodies if user refreshes
        document.querySelectorAll('#mwpl-analysis-table tbody').forEach(tb => {
            if (tb.id !== 'mwpl-analysis-body') {
                tb.remove();
            }
        });

        if (!data || Object.keys(data).length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#888;">No historical MWPL data found.</td></tr>';
            return;
        }

        // Dynamically get client names from the latest data of the first symbol
        let clientNames = new Set();
        Object.values(data).forEach(rows => {
            rows.forEach(r => {
                if (r.mwpl_array && Array.isArray(r.mwpl_array)) {
                    r.mwpl_array.forEach(item => {
                        clientNames.add(Object.keys(item)[0]);
                    });
                }
            });
        });
        clientNames = Array.from(clientNames);

        // Update thead dynamically
        let clientHeaders = clientNames.map(c => `<th style="padding: 8px;">${c}</th>`).join('');
        thead.innerHTML = `
            <tr>
                <th style="padding: 8px; width: 120px;">Symbol</th>
                <th style="padding: 8px; width: 100px;">Date</th>
                <th style="padding: 8px; width: 80px;">EQ Close</th>
                <th style="padding: 8px; width: 80px;">% Chg</th>
                <th style="padding: 8px; width: 80px;">Fut Close</th>
                <th style="padding: 8px; width: 80px;">Total MWPL</th>
                <th style="padding: 8px; width: 80px;">Total % Chg</th>
                ${clientHeaders}
            </tr>
        `;

        // Sort symbols by latest MWPL Total descending
        const symbolsList = Object.keys(data).map(sym => {
            const rows = data[sym].sort((a, b) => new Date(b.date) - new Date(a.date));
            const latest = rows[0];
            let total = 0;
            if (latest.mwpl_array && Array.isArray(latest.mwpl_array)) {
                latest.mwpl_array.forEach(item => {
                    const val = parseFloat(Object.values(item)[0]);
                    total += isNaN(val) ? 0 : val;
                });
            } else if (latest.mwpl) {
                 total = parseFloat(latest.mwpl);
            }

            return { sym, rows, latest, total };
        }).sort((a, b) => b.total - a.total);

        symbolsList.forEach(itemData => {
            const { sym, rows, latest, total } = itemData;

            // Generate unique ID for the sub-rows block
            const blockId = `mwpl-block-${sym}`;

            // Create a dedicated tbody for this symbol to keep main and history rows together
            const symbolTbody = document.createElement('tbody');

            // Main Symbol Row
            const mainTr = document.createElement('tr');
            mainTr.style.cursor = 'pointer';
            mainTr.style.borderTop = '1px solid #444';
            mainTr.onclick = () => {
                const block = document.getElementById(blockId);
                if (block.style.display === 'none') {
                    block.style.display = 'table-row-group';
                    mainTr.querySelector('.expand-icon').innerText = '▼';
                } else {
                    block.style.display = 'none';
                    mainTr.querySelector('.expand-icon').innerText = '▶';
                }
            };

            let mainClientTds = '';
            clientNames.forEach(c => {
                let cVal = '-';
                if (latest.mwpl_array) {
                    const found = latest.mwpl_array.find(item => Object.keys(item)[0] === c);
                    if (found) cVal = Object.values(found)[0].toFixed(2) + '%';
                }
                mainClientTds += `<td style="color: #aaa;">${cVal}</td>`;
            });

            // Compare with previous day to determine color
            let eqColor = '#ddd';
            let eqChgColor = '#aaa';
            let futColor = '#ddd';
            let totalColor = '#60a5fa'; // default
            let totalChgColor = '#aaa';
            let eqArrow = '';
            let eqChgStr = '-';
            let futArrow = '';
            let totalArrow = '';
            let totalChgStr = '-';

            if (rows.length > 1) {
                const prev = rows[1]; // Since rows are sorted descending by date

                if (prev.eq_close !== 0) {
                    const pctChg = ((latest.eq_close - prev.eq_close) / Math.abs(prev.eq_close)) * 100;
                    eqChgStr = pctChg > 0 ? '+' + pctChg.toFixed(2) + '%' : pctChg.toFixed(2) + '%';
                    if (pctChg > 0) eqChgColor = '#60a5fa';
                    else if (pctChg < 0) eqChgColor = '#ff4d4d';
                } else if (latest.eq_close > 0) {
                    eqChgStr = '+100.00%';
                    eqChgColor = '#60a5fa';
                }

                if (latest.eq_close > prev.eq_close) { eqColor = '#60a5fa'; eqArrow = '▲'; }
                else if (latest.eq_close < prev.eq_close) { eqColor = '#ff4d4d'; eqArrow = '▼'; }

                if (latest.fut1_close > prev.fut1_close) { futColor = '#60a5fa'; futArrow = '▲'; }
                else if (latest.fut1_close < prev.fut1_close) { futColor = '#ff4d4d'; futArrow = '▼'; }

                let prevTotal = 0;
                if (prev.mwpl_array && Array.isArray(prev.mwpl_array)) {
                    prev.mwpl_array.forEach(item => {
                        prevTotal += parseFloat(Object.values(item)[0]) || 0;
                    });
                } else if (prev.mwpl) {
                    prevTotal = parseFloat(prev.mwpl);
                }

                if (prevTotal !== 0) {
                    const pctChg = ((total - prevTotal) / Math.abs(prevTotal)) * 100;
                    totalChgStr = pctChg > 0 ? '+' + pctChg.toFixed(2) + '%' : pctChg.toFixed(2) + '%';
                    if (pctChg > 0) totalChgColor = '#60a5fa';
                    else if (pctChg < 0) totalChgColor = '#ff4d4d';
                } else if (total > 0) {
                    totalChgStr = '+100.00%';
                    totalChgColor = '#60a5fa';
                }

                if (total > prevTotal) { totalColor = '#60a5fa'; totalArrow = '▲'; }
                else if (total < prevTotal) { totalColor = '#ff4d4d'; totalArrow = '▼'; }
            }

            // if totally over 20%, make total red
            if (total > 20) {
                totalColor = '#ff4d4d';
            }

            mainTr.innerHTML = `
                <td style="font-weight: bold;"><span class="expand-icon" style="display:inline-block; width:20px; color:#888;">▶</span>${sym}</td>
                <td>${latest.date} <span style="font-size: 10px; color: #888;">(Latest)</span></td>
                <td style="color: ${eqColor};">${latest.eq_close ? latest.eq_close.toFixed(2) : '-'} <span style="font-size:0.8em">${eqArrow}</span></td>
                <td style="color: ${eqChgColor}; font-weight: bold;">${eqChgStr}</td>
                <td style="color: ${futColor};">${latest.fut1_close ? latest.fut1_close.toFixed(2) : '-'} <span style="font-size:0.8em">${futArrow}</span></td>
                <td style="color: ${totalColor}; font-weight: bold;">${total.toFixed(2)}% <span style="font-size:0.8em">${totalArrow}</span></td>
                <td style="color: ${totalChgColor}; font-weight: bold;">${totalChgStr}</td>
                ${mainClientTds}
            `;
            symbolTbody.appendChild(mainTr);

            // History Rows Block
            const tbodyBlock = document.createElement('tbody');
            tbodyBlock.id = blockId;
            tbodyBlock.style.display = 'none';

            rows.forEach((r, idx) => {
                if (idx === 0) return; // skip latest since it's above

                const historyTr = document.createElement('tr');
                historyTr.style.backgroundColor = '#1a1a1a';

                let rowTotal = 0;
                if (r.mwpl_array && Array.isArray(r.mwpl_array)) {
                    r.mwpl_array.forEach(item => {
                        const val = parseFloat(Object.values(item)[0]) || 0;
                        rowTotal += val;
                    });
                } else if (r.mwpl) {
                    rowTotal = parseFloat(r.mwpl);
                }

                let clientTds = '';
                clientNames.forEach(c => {
                    let cVal = '-';
                    if (r.mwpl_array) {
                        const found = r.mwpl_array.find(item => Object.keys(item)[0] === c);
                        if (found) cVal = Object.values(found)[0].toFixed(2) + '%';
                    }
                    clientTds += `<td style="color: #aaa;">${cVal}</td>`;
                });

                let histEqColor = '#ddd';
                let histEqChgColor = '#aaa';
                let histFutColor = '#ddd';
                let histTotalColor = '#7dd3fc';
                let histTotalChgColor = '#aaa';
                let histEqArrow = '';
                let histEqChgStr = '-';
                let histFutArrow = '';
                let histTotalArrow = '';
                let histTotalChgStr = '-';

                if (idx < rows.length - 1) {
                    const histPrev = rows[idx + 1];

                    if (histPrev.eq_close !== 0) {
                        const pctChg = ((r.eq_close - histPrev.eq_close) / Math.abs(histPrev.eq_close)) * 100;
                        histEqChgStr = pctChg > 0 ? '+' + pctChg.toFixed(2) + '%' : pctChg.toFixed(2) + '%';
                        if (pctChg > 0) histEqChgColor = '#60a5fa';
                        else if (pctChg < 0) histEqChgColor = '#ff4d4d';
                    } else if (r.eq_close > 0) {
                        histEqChgStr = '+100.00%';
                        histEqChgColor = '#60a5fa';
                    }

                    if (r.eq_close > histPrev.eq_close) { histEqColor = '#60a5fa'; histEqArrow = '▲'; }
                    else if (r.eq_close < histPrev.eq_close) { histEqColor = '#ff4d4d'; histEqArrow = '▼'; }

                    if (r.fut1_close > histPrev.fut1_close) { histFutColor = '#60a5fa'; histFutArrow = '▲'; }
                    else if (r.fut1_close < histPrev.fut1_close) { histFutColor = '#ff4d4d'; histFutArrow = '▼'; }

                    let histPrevTotal = 0;
                    if (histPrev.mwpl_array && Array.isArray(histPrev.mwpl_array)) {
                        histPrev.mwpl_array.forEach(item => {
                            histPrevTotal += parseFloat(Object.values(item)[0]) || 0;
                        });
                    } else if (histPrev.mwpl) {
                        histPrevTotal = parseFloat(histPrev.mwpl);
                    }

                    if (histPrevTotal !== 0) {
                        const pctChg = ((rowTotal - histPrevTotal) / Math.abs(histPrevTotal)) * 100;
                        histTotalChgStr = pctChg > 0 ? '+' + pctChg.toFixed(2) + '%' : pctChg.toFixed(2) + '%';
                        if (pctChg > 0) histTotalChgColor = '#60a5fa';
                        else if (pctChg < 0) histTotalChgColor = '#ff4d4d';
                    } else if (rowTotal > 0) {
                        histTotalChgStr = '+100.00%';
                        histTotalChgColor = '#60a5fa';
                    }

                    if (rowTotal > histPrevTotal) { histTotalColor = '#60a5fa'; histTotalArrow = '▲'; }
                    else if (rowTotal < histPrevTotal) { histTotalColor = '#ff4d4d'; histTotalArrow = '▼'; }
                }

                if (rowTotal > 20) {
                    histTotalColor = '#ff4d4d';
                }

                historyTr.innerHTML = `
                    <td style="padding-left: 30px; color: #bbb;">└ ${r.date}</td>
                    <td style="color: #ddd;">${r.date}</td>
                    <td style="color: ${histEqColor};">${r.eq_close ? r.eq_close.toFixed(2) : '-'} <span style="font-size:0.8em">${histEqArrow}</span></td>
                    <td style="color: ${histEqChgColor};">${histEqChgStr}</td>
                    <td style="color: ${histFutColor};">${r.fut1_close ? r.fut1_close.toFixed(2) : '-'} <span style="font-size:0.8em">${histFutArrow}</span></td>
                    <td style="color: ${histTotalColor};">${rowTotal.toFixed(2)}% <span style="font-size:0.8em">${histTotalArrow}</span></td>
                    <td style="color: ${histTotalChgColor};">${histTotalChgStr}</td>
                    ${clientTds}
                `;
                tbodyBlock.appendChild(historyTr);
            });

            // Append the main row's tbody, then the history block's tbody immediately after
            tbody.parentElement.appendChild(symbolTbody);
            tbody.parentElement.appendChild(tbodyBlock);
        });

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:red;">Error: ${e.message}</td></tr>`;
    }

    if (loadBtn) {
        loadBtn.disabled = false;
        loadBtn.innerHTML = originalText;
    }
}
