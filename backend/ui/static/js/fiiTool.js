async function loadFiiAnalysis() {
    console.log("Loading FII Analysis Tab Data...");
    try {
        const days = document.getElementById('fii-analysis-days')?.value || '30';

        // Load Cash Flow
        const cashRes = await fetch(`/api/market-activity/cash-flow?days=${days}`);
        const cashData = await cashRes.json();
        if (window.fiiDiiTabChartInstance) window.fiiDiiTabChartInstance.destroy();
        const ctx = document.getElementById('fiiDiiTabChart').getContext('2d');
        window.fiiDiiTabChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: cashData.dates,
                datasets: [
                    { label: 'FII Net', data: cashData.fii_net, backgroundColor: '#3176B8' },
                    { label: 'DII Net', data: cashData.dii_net, backgroundColor: '#ff9800' }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#ccc' } } },
                scales: {
                    x: { stacked: true, ticks: { color: '#aaa' }, grid: { color: '#333' } },
                    y: { stacked: true, ticks: { color: '#aaa' }, grid: { color: '#333' } }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                }
            }
        });

        // Load Participant Contracts for Smart Money History Table
        const partRes = await fetch(`/api/market-activity/participant-oi?days=${days}`);
        const partData = await partRes.json();
        renderFiiSmartMoneyHistoryTable(partData);

        // Load FII Money Stats for FII Position Table
        const moneyRes = await fetch(`/api/market-activity/fii-stats-money?days=${days}`);
        const moneyData = await moneyRes.json();
        renderFiiPositionHistoryTable(partData, moneyData);


    } catch (e) {
        console.error("Error loading FII Analysis", e);
    }
}

window.toggleFiiSmartMoneyHistory = function(blockId) {
    const rows = document.querySelectorAll(`tr.${blockId}`);
    if (rows.length === 0) return;
    const isHidden = rows[0].style.display === 'none';

    rows.forEach(row => {
        row.style.display = isHidden ? '' : 'none';
    });

    const icon = document.getElementById('icon-' + blockId);
    if (icon) {
        icon.className = isHidden ? 'fas fa-chevron-down' : 'fas fa-chevron-right';
    }
};

function renderFiiSmartMoneyHistoryTable(data) {
    const dates = data.dates || [];
    const tbody = document.getElementById('fii-smart-money-history-body');
    if (!tbody) return;

    if (dates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="15" style="text-align:center; color:#888;">No historical data available.</td></tr>';
        return;
    }

    // Clean up old dynamically created tbodies if user reloads
    document.querySelectorAll('#fii-smart-money-history-table tbody').forEach(tb => {
        if (tb.id !== 'fii-smart-money-history-body') {
            tb.remove();
        }
    });

    tbody.innerHTML = '';

    const metrics = [
        { key: 'fut_idx', label: 'Index Futures' },
        { key: 'fut_stk', label: 'Stock Futures' },
        { key: 'opt_idx_ce', label: 'Index Calls' },
        { key: 'opt_idx_pe', label: 'Index Puts' },
        { key: 'opt_stk_ce', label: 'Stock Calls' },
        { key: 'opt_stk_pe', label: 'Stock Puts' }
    ];

    const formatNum = (val) => {
        if (val == null || isNaN(val)) return '-';
        return parseInt(val).toLocaleString();
    };

    const getColor = (val) => {
        if (val > 0) return '#60a5fa'; // Blue for positive
        if (val < 0) return '#ff4d4d'; // Red for negative
        return '#ccc';
    };

    metrics.forEach(m => {
        // Latest data (last element in array)
        const latestIdx = dates.length - 1;

        // Helper to extract values
        const getVal = (prefix, participant, idx) => data[`${participant}_${m.key}${prefix}`]?.[idx] || 0;

        const latestFiiL = getVal('_long', 'fii', latestIdx);
        const latestFiiS = getVal('_short', 'fii', latestIdx);
        const latestFiiN = getVal('', 'fii', latestIdx);

        const latestDiiL = getVal('_long', 'dii', latestIdx);
        const latestDiiS = getVal('_short', 'dii', latestIdx);
        const latestDiiN = getVal('', 'dii', latestIdx);

        const latestProL = getVal('_long', 'pro', latestIdx);
        const latestProS = getVal('_short', 'pro', latestIdx);
        const latestProN = getVal('', 'pro', latestIdx);

        const latestCliL = getVal('_long', 'client', latestIdx);
        const latestCliS = getVal('_short', 'client', latestIdx);
        const latestCliN = getVal('', 'client', latestIdx);

        // Create an individual tbody for each instrument block
        const blockId = `fii-smart-money-hist-${m.key}`;
        let blockHTML = `<tbody id="fii-tbody-${m.key}">`;

        blockHTML += `
            <tr style="cursor: pointer; background: #222;" onclick="toggleFiiSmartMoneyHistory('${blockId}')">
                <td style="text-align:center;"><i class="fas fa-chevron-right" id="icon-${blockId}" style="color:#888; font-size:10px;"></i></td>
                <td style="font-weight: bold; color: #fff;">${m.label}</td>
                <td>${dates[latestIdx]}</td>

                <td style="color: #60a5fa;">${formatNum(latestFiiL)}</td>
                <td style="color: #ff4d4d;">${formatNum(latestFiiS)}</td>
                <td style="color: ${getColor(latestFiiN)}; border-right: 1px solid #444;">${formatNum(latestFiiN)}</td>

                <td style="color: #60a5fa;">${formatNum(latestDiiL)}</td>
                <td style="color: #ff4d4d;">${formatNum(latestDiiS)}</td>
                <td style="color: ${getColor(latestDiiN)}; border-right: 1px solid #444;">${formatNum(latestDiiN)}</td>

                <td style="color: #60a5fa;">${formatNum(latestProL)}</td>
                <td style="color: #ff4d4d;">${formatNum(latestProS)}</td>
                <td style="color: ${getColor(latestProN)}; border-right: 1px solid #444;">${formatNum(latestProN)}</td>

                <td style="color: #60a5fa;">${formatNum(latestCliL)}</td>
                <td style="color: #ff4d4d;">${formatNum(latestCliS)}</td>
                <td style="color: ${getColor(latestCliN)};">${formatNum(latestCliN)}</td>
            </tr>
        `;

        // Historical rows (hidden by default)
        for (let i = latestIdx - 1; i >= 0; i--) {
            const fiiL = getVal('_long', 'fii', i);
            const fiiS = getVal('_short', 'fii', i);
            const fiiN = getVal('', 'fii', i);

            const diiL = getVal('_long', 'dii', i);
            const diiS = getVal('_short', 'dii', i);
            const diiN = getVal('', 'dii', i);

            const proL = getVal('_long', 'pro', i);
            const proS = getVal('_short', 'pro', i);
            const proN = getVal('', 'pro', i);

            const cliL = getVal('_long', 'client', i);
            const cliS = getVal('_short', 'client', i);
            const cliN = getVal('', 'client', i);

            blockHTML += `
                <tr class="${blockId}" style="display: none; background: #1a1a1a;">
                    <td></td>
                    <td style="color: #aaa; padding-left: 20px;">${m.label}</td>
                    <td style="color: #888;">${dates[i]}</td>

                    <td style="color: #60a5fa;">${formatNum(fiiL)}</td>
                    <td style="color: #ff4d4d;">${formatNum(fiiS)}</td>
                    <td style="color: ${getColor(fiiN)}; border-right: 1px solid #444;">${formatNum(fiiN)}</td>

                    <td style="color: #60a5fa;">${formatNum(diiL)}</td>
                    <td style="color: #ff4d4d;">${formatNum(diiS)}</td>
                    <td style="color: ${getColor(diiN)}; border-right: 1px solid #444;">${formatNum(diiN)}</td>

                    <td style="color: #60a5fa;">${formatNum(proL)}</td>
                    <td style="color: #ff4d4d;">${formatNum(proS)}</td>
                    <td style="color: ${getColor(proN)}; border-right: 1px solid #444;">${formatNum(proN)}</td>

                    <td style="color: #60a5fa;">${formatNum(cliL)}</td>
                    <td style="color: #ff4d4d;">${formatNum(cliS)}</td>
                    <td style="color: ${getColor(cliN)};">${formatNum(cliN)}</td>
                </tr>
            `;
        }
        blockHTML += `</tbody>`;
        document.getElementById('fii-smart-money-history-table').insertAdjacentHTML('beforeend', blockHTML);
    });
}


window.toggleFiiPositionHistory = function(blockId) {
    const rows = document.querySelectorAll(`tr.${blockId}`);
    if (rows.length === 0) return;
    const isHidden = rows[0].style.display === 'none';

    rows.forEach(row => {
        row.style.display = isHidden ? '' : 'none';
    });

    const icon = document.getElementById('icon-' + blockId);
    if (icon) {
        icon.className = isHidden ? 'fas fa-chevron-down' : 'fas fa-chevron-right';
    }
};

function renderFiiPositionHistoryTable(partData, moneyData) {
    const dates = partData.dates || [];
    const tbody = document.getElementById('fii-position-history-body');
    if (!tbody) return;

    if (dates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#888;">No historical data available.</td></tr>';
        return;
    }

    // Clean up old dynamically created tbodies if user reloads
    document.querySelectorAll('#fii-position-history-table tbody').forEach(tb => {
        if (tb.id !== 'fii-position-history-body') {
            tb.remove();
        }
    });

    tbody.innerHTML = '';

    const metrics = [
        { key: 'fut_idx', label: 'Index Futures', moneyKey: 'fut_idx' },
        { key: 'fut_stk', label: 'Stock Futures', moneyKey: 'fut_stk' },
        { key: 'opt_idx_ce', label: 'Index Calls', moneyKey: 'opt_idx' }, // Note: Money data groups options CE/PE
        { key: 'opt_idx_pe', label: 'Index Puts', moneyKey: 'opt_idx' },
        { key: 'opt_stk_ce', label: 'Stock Calls', moneyKey: 'opt_stk' },
        { key: 'opt_stk_pe', label: 'Stock Puts', moneyKey: 'opt_stk' }
    ];

    const formatNum = (val) => {
        if (val == null || isNaN(val)) return '-';
        return parseInt(val).toLocaleString();
    };

    const formatMoney = (val) => {
        if (val == null || isNaN(val)) return '-';
        return '₹' + parseInt(val).toLocaleString() + ' Cr';
    };

    const getColor = (val) => {
        if (val > 0) return '#60a5fa'; // Blue for positive
        if (val < 0) return '#ff4d4d'; // Red for negative
        return '#ccc';
    };

    metrics.forEach(m => {
        // Latest data (last element in array)
        const latestIdx = dates.length - 1;

        // Helper to extract values
        const getVal = (prefix, participant, idx) => partData[`${participant}_${m.key}${prefix}`]?.[idx] || 0;

        // Match money data date. Note: Money data might not have the same exact dates if missing, so we find by date string.
        const moneyDates = moneyData.dates || [];

        const getMoneyVal = (idx) => {
            const dateStr = dates[idx];
            const mIdx = moneyDates.indexOf(dateStr);
            if (mIdx === -1) return 0;
            // For options, since money data groups them, we divide by 2 for display purposes here or just show the combined for both CE and PE rows.
            // Let's just show the combined money for that instrument type, with a note if possible. But for simplicity, we'll just pull it.
            let val = moneyData[m.moneyKey]?.[mIdx] || 0;
            return val;
        };


        const latestFiiL = getVal('_long', 'fii', latestIdx);
        const latestFiiS = getVal('_short', 'fii', latestIdx);
        const latestFiiN = getVal('', 'fii', latestIdx);
        let latestFiiMoney = getMoneyVal(latestIdx);
        if (m.key.includes('_pe')) latestFiiMoney = 0; // Avoid double counting money if displaying combined for both CE/PE. We'll show money on CE row or just show for both. Let's show for both for now, or maybe only for CE. Let's just show it. Actually, wait.
        // If moneyKey is opt_idx, it means total options. Let's show it only on the CE row to avoid confusion, or better, calculate it properly if backend supports it. Backend doesn't support CE/PE money split.
        // I will show it on all rows, but users should know it's grouped.
        // Actually, FII position table only needs FII data.

        const blockId = `fii-position-hist-${m.key}`;
        let blockHTML = `<tbody id="fii-pos-tbody-${m.key}">`;

        let moneyDisplay = formatMoney(latestFiiMoney);
        if (m.key.includes('_pe') || m.key.includes('_ce')) {
            moneyDisplay = (m.key.includes('_ce') ? formatMoney(latestFiiMoney) + " (CE+PE)" : "-");
        }

        blockHTML += `
            <tr style="cursor: pointer; background: #222;" onclick="toggleFiiPositionHistory('${blockId}')">
                <td style="text-align:center;"><i class="fas fa-chevron-right" id="icon-${blockId}" style="color:#888; font-size:10px;"></i></td>
                <td style="font-weight: bold; color: #fff;">${m.label}</td>
                <td>${dates[latestIdx]}</td>

                <td style="color: #60a5fa;">${formatNum(latestFiiL)}</td>
                <td style="color: #ff4d4d;">${formatNum(latestFiiS)}</td>
                <td style="color: ${getColor(latestFiiN)}; border-right: 1px solid #444;">${formatNum(latestFiiN)}</td>
                <td style="color: ${getColor(latestFiiMoney)};">${moneyDisplay}</td>
            </tr>
        `;

        // Historical rows (hidden by default)
        for (let i = latestIdx - 1; i >= 0; i--) {
            const fiiL = getVal('_long', 'fii', i);
            const fiiS = getVal('_short', 'fii', i);
            const fiiN = getVal('', 'fii', i);
            let fiiMoney = getMoneyVal(i);

            let mDisplay = formatMoney(fiiMoney);
            if (m.key.includes('_pe') || m.key.includes('_ce')) {
                mDisplay = (m.key.includes('_ce') ? formatMoney(fiiMoney) + " (CE+PE)" : "-");
            }


            blockHTML += `
                <tr class="${blockId}" style="display: none; background: #1a1a1a;">
                    <td></td>
                    <td style="color: #aaa; padding-left: 20px;">${m.label}</td>
                    <td style="color: #888;">${dates[i]}</td>

                    <td style="color: #60a5fa;">${formatNum(fiiL)}</td>
                    <td style="color: #ff4d4d;">${formatNum(fiiS)}</td>
                    <td style="color: ${getColor(fiiN)}; border-right: 1px solid #444;">${formatNum(fiiN)}</td>
                    <td style="color: ${getColor(fiiMoney)};">${mDisplay}</td>
                </tr>
            `;
        }
        blockHTML += `</tbody>`;
        document.getElementById('fii-position-history-table').insertAdjacentHTML('beforeend', blockHTML);
    });
}
