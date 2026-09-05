async function loadFiiAnalysis(event = null) {
    console.log("Loading FII Analysis Tab Data...");
    const btn = document.getElementById('btn-load-fii');
    let originalText = '';
    if (btn) {
        originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        btn.disabled = true;
    }

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

        // Load Granular FII Stats to embed in Participant OI table
        const granularRes = await fetch(`/api/market-activity/fii-stats-granular?days=${days}`);
        const granularData = await granularRes.json();

        // Pass granularData along with partData to render it embedded
        renderFiiSmartMoneyHistoryTable(partData, granularData);

        // Load Trend Chart
        await loadFiiTrendChart(days);

    } catch (e) {
        console.error("Error loading FII Analysis", e);
    } finally {
        if (btn) {
            btn.innerHTML = originalText || '<i class="fas fa-sync"></i> Refresh FII Data';
            btn.disabled = false;
        }
    }
}

window.loadFiiTrendChart = async function(overrideDays) {
    console.log("Loading FII Trend Chart...");
    try {
        let validOverrideDays = (overrideDays !== undefined && typeof overrideDays !== "object" && typeof overrideDays !== "boolean" && String(overrideDays) !== "[object Event]" && !(overrideDays instanceof Event)) ? overrideDays : null;
        const days = validOverrideDays || document.getElementById("fii-trend-lookback")?.value || document.getElementById("fii-analysis-days")?.value || "30";
        const symbol = document.getElementById('fii-analysis-index-symbol')?.value?.trim().toUpperCase() || 'NIFTY';
        const expiryOnly = document.getElementById('fii-opt-expiry-only')?.checked ? 'true' : 'false';
        const combinedOi = document.getElementById('fii-opt-combined-oi')?.checked ? 'true' : 'false';

        const pcrContainer = document.getElementById('fii-trend-chart-container');

        if (!window.fiiTrendChartInstance) window.fiiTrendChartInstance = echarts.init(pcrContainer);
        window.fiiTrendChartInstance.showLoading({ text: 'Loading...', color: '#60a5fa', maskColor: 'rgba(30, 30, 30, 0.8)' });

        const res = await fetch(`/api/data/derivatives/pcr_history?symbol=${symbol}&days=${days}&expiry_only=${expiryOnly}`);
        const data = await res.json();

        window.fiiTrendChartInstance.hideLoading();

        if (!data.dates || data.dates.length === 0) {
            window.fiiTrendChartInstance.clear();
            return;
        }

        const showCombinedOi = combinedOi === 'true';

        // Render PCR Chart (Price vs OI vs PCR)
        const dates = data.dates;
        const prices = data.price;
        const pcrs = data.pcr;
        const oiData = showCombinedOi ? data.total_oi : data.fut_oi;
        const oiSeriesName = showCombinedOi ? 'Combined OI' : 'Futures OI';

        const pcrOption = {
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
            legend: { data: [oiSeriesName, 'Close Price', 'PCR'], textStyle: { color: '#ccc' }, top: 0 },
            grid: { left: '5%', right: '10%', bottom: '10%', top: '15%', containLabel: true },
            xAxis: { type: 'category', data: dates, axisLabel: { color: '#888' } },
            yAxis: [
                { type: 'value', name: 'Close', position: 'left', axisLabel: { color: '#888' }, splitLine: { show: false }, scale: true },
                { type: 'value', name: 'PCR', position: 'right', axisLabel: { color: '#888' }, splitLine: { show: false } },
                { type: 'value', name: 'OI', position: 'right', offset: 50, axisLabel: { color: '#888', formatter: (val) => (val/100000).toFixed(1) + 'L' }, splitLine: { show: false }, min: 0 }
            ],
            dataZoom: [{ type: 'inside' }, { type: 'slider', textStyle: { color: '#ccc' } }],
            series: [
                {
                    name: oiSeriesName,
                    type: 'bar',
                    data: oiData,
                    yAxisIndex: 2,
                    itemStyle: { color: '#3176B8' }, // FII Net Blue
                    barMaxWidth: 30
                },
                {
                    name: 'Close Price',
                    type: 'line',
                    data: prices,
                    yAxisIndex: 0,
                    itemStyle: { color: '#ffffff' },
                    lineStyle: { width: 2 },
                    showSymbol: false
                },
                {
                    name: 'PCR',
                    type: 'line',
                    data: pcrs,
                    yAxisIndex: 1,
                    itemStyle: { color: '#ff9800' },
                    lineStyle: { width: 2, type: 'dashed' },
                    showSymbol: false
                }
            ]
        };

        window.fiiTrendChartInstance.setOption(pcrOption, true);

    } catch (e) {
        console.error("Error loading FII Trend Chart", e);
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

function renderFiiSmartMoneyHistoryTable(data, granularData) {
    const dates = data.dates || [];
    const tbody = document.getElementById('fii-smart-money-history-body');
    if (!tbody) return;

    if (dates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="22" style="text-align:center; color:#888;">No historical data available.</td></tr>';
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
        { key: 'fut_idx', label: 'Index Futures', granularLabel: 'INDEX FUTURES' },
        { key: 'fut_stk', label: 'Stock Futures', granularLabel: 'STOCK FUTURES' },
        { key: 'opt_idx_ce', label: 'Index Calls', granularLabel: 'INDEX OPTIONS' },
        { key: 'opt_idx_pe', label: 'Index Puts', granularLabel: 'INDEX OPTIONS' },
        { key: 'opt_stk_ce', label: 'Stock Calls', granularLabel: 'STOCK OPTIONS' },
        { key: 'opt_stk_pe', label: 'Stock Puts', granularLabel: 'STOCK OPTIONS' }
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

    const getRatio = (long, short) => {
        if (!long || !short || short === 0) return '-';
        return (long / short).toFixed(2);
    };

    metrics.forEach(m => {
        const latestIdx = dates.length - 1;
        const getVal = (prefix, participant, idx) => data[`${participant}_${m.key}${prefix}`]?.[idx] || 0;

        const blockId = `fii-smart-money-hist-${m.key}`;
        let blockHTML = `<tbody id="fii-tbody-${m.key}">`;

        for (let i = latestIdx; i >= 0; i--) {
            const isLatest = i === latestIdx;
            const dateStr = dates[i];

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

            // Fetch granular FII data for this specific instrument and date
            const granular = (granularData?.data_by_date?.[dateStr] || []).find(x => x.instrument_type === m.granularLabel);
            const fiiBuyC = granular ? granular.buy_contracts : null;
            const fiiSellC = granular ? granular.sell_contracts : null;
            const fiiNetC = granular ? granular.net_contracts : null;

            if (isLatest) {
                // Parent row for the latest date (always visible)
                blockHTML += `
                    <tr style="cursor: pointer; background: #222;" onclick="toggleFiiSmartMoneyHistory('${blockId}')">
                        <td style="text-align:center;"><i class="fas fa-chevron-right" id="icon-${blockId}" style="color:#888; font-size:10px;"></i></td>
                        <td style="font-weight: bold; color: #fff;">${m.label}</td>
                        <td>${dateStr}</td>

                        <td style="color: #60a5fa;">${formatNum(fiiL)}</td>
                        <td style="color: #ff4d4d;">${formatNum(fiiS)}</td>
                        <td style="color: ${getColor(fiiN)};">${formatNum(fiiN)}</td>
                        <td style="color: #bbb;">${getRatio(fiiL, fiiS)}</td>
                        <td style="color: #ffeb3b;">${formatNum(fiiBuyC)}</td>
                        <td style="color: #ffeb3b;">${formatNum(fiiSellC)}</td>
                        <td style="color: ${getColor(fiiNetC)}; border-right: 1px solid #444;">${formatNum(fiiNetC)}</td>

                        <td style="color: #60a5fa;">${formatNum(diiL)}</td>
                        <td style="color: #ff4d4d;">${formatNum(diiS)}</td>
                        <td style="color: ${getColor(diiN)};">${formatNum(diiN)}</td>
                        <td style="color: #bbb; border-right: 1px solid #444;">${getRatio(diiL, diiS)}</td>

                        <td style="color: #60a5fa;">${formatNum(proL)}</td>
                        <td style="color: #ff4d4d;">${formatNum(proS)}</td>
                        <td style="color: ${getColor(proN)};">${formatNum(proN)}</td>
                        <td style="color: #bbb; border-right: 1px solid #444;">${getRatio(proL, proS)}</td>

                        <td style="color: #60a5fa;">${formatNum(cliL)}</td>
                        <td style="color: #ff4d4d;">${formatNum(cliS)}</td>
                        <td style="color: ${getColor(cliN)};">${formatNum(cliN)}</td>
                        <td style="color: #bbb;">${getRatio(cliL, cliS)}</td>
                    </tr>
                `;

                // Add granular index sub-rows if applicable
                if (m.key === 'fut_idx' || m.key === 'opt_idx_ce' || m.key === 'opt_idx_pe') {
                    const specificIndexes = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'NIFTYNXT50'];
                    const labelSuffix = m.key === 'fut_idx' ? 'FUTURES' : 'OPTIONS';

                    specificIndexes.forEach(idxName => {
                        const subInstrName = `${idxName} ${labelSuffix}`;
                        const subGranular = (granularData?.data_by_date?.[dateStr] || []).find(x => x.instrument_type === subInstrName);

                        if (subGranular) {
                            const subBuyC = subGranular.buy_contracts;
                            const subSellC = subGranular.sell_contracts;
                            const subNetC = subGranular.net_contracts;
                            const subOiC = subGranular.oi_contracts;

                            blockHTML += `
                                <tr class="${blockId}" style="display: none; background: #1a1a1a; font-size: 11px;">
                                    <td></td>
                                    <td style="color: #999; padding-left: 20px;">- ${idxName}</td>
                                    <td style="color: #888;">${dateStr}</td>

                                    <td style="color: #60a5fa;">-</td>
                                    <td style="color: #ff4d4d;">-</td>
                                    <td style="color: #ccc;">-</td>
                                    <td style="color: #bbb;">-</td>
                                    <td style="color: #ffeb3b;">${formatNum(subBuyC)}</td>
                                    <td style="color: #ffeb3b;">${formatNum(subSellC)}</td>
                                    <td style="color: ${getColor(subNetC)}; border-right: 1px solid #444;">${formatNum(subNetC)}</td>

                                    <td colspan="12" style="color: #666; text-align: center;">Not available for specific indexes</td>
                                </tr>
                            `;
                        }
                    });
                }
            } else {
                // Historical row (hidden by default)
                blockHTML += `
                    <tr class="${blockId}" style="display: none; background: #1a1a1a;">
                        <td></td>
                        <td style="color: #aaa; padding-left: 20px;">${m.label}</td>
                        <td style="color: #888;">${dateStr}</td>

                        <td style="color: #60a5fa;">${formatNum(fiiL)}</td>
                        <td style="color: #ff4d4d;">${formatNum(fiiS)}</td>
                        <td style="color: ${getColor(fiiN)};">${formatNum(fiiN)}</td>
                        <td style="color: #bbb;">${getRatio(fiiL, fiiS)}</td>
                        <td style="color: #ffeb3b;">${formatNum(fiiBuyC)}</td>
                        <td style="color: #ffeb3b;">${formatNum(fiiSellC)}</td>
                        <td style="color: ${getColor(fiiNetC)}; border-right: 1px solid #444;">${formatNum(fiiNetC)}</td>

                        <td style="color: #60a5fa;">${formatNum(diiL)}</td>
                        <td style="color: #ff4d4d;">${formatNum(diiS)}</td>
                        <td style="color: ${getColor(diiN)};">${formatNum(diiN)}</td>
                        <td style="color: #bbb; border-right: 1px solid #444;">${getRatio(diiL, diiS)}</td>

                        <td style="color: #60a5fa;">${formatNum(proL)}</td>
                        <td style="color: #ff4d4d;">${formatNum(proS)}</td>
                        <td style="color: ${getColor(proN)};">${formatNum(proN)}</td>
                        <td style="color: #bbb; border-right: 1px solid #444;">${getRatio(proL, proS)}</td>

                        <td style="color: #60a5fa;">${formatNum(cliL)}</td>
                        <td style="color: #ff4d4d;">${formatNum(cliS)}</td>
                        <td style="color: ${getColor(cliN)};">${formatNum(cliN)}</td>
                        <td style="color: #bbb;">${getRatio(cliL, cliS)}</td>
                    </tr>
                `;

                // Add granular index sub-rows if applicable for historical rows
                if (m.key === 'fut_idx' || m.key === 'opt_idx_ce' || m.key === 'opt_idx_pe') {
                    const specificIndexes = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'NIFTYNXT50'];
                    const labelSuffix = m.key === 'fut_idx' ? 'FUTURES' : 'OPTIONS';

                    specificIndexes.forEach(idxName => {
                        const subInstrName = `${idxName} ${labelSuffix}`;
                        const subGranular = (granularData?.data_by_date?.[dateStr] || []).find(x => x.instrument_type === subInstrName);

                        if (subGranular) {
                            const subBuyC = subGranular.buy_contracts;
                            const subSellC = subGranular.sell_contracts;
                            const subNetC = subGranular.net_contracts;
                            const subOiC = subGranular.oi_contracts;

                            blockHTML += `
                                <tr class="${blockId}" style="display: none; background: #141414; font-size: 11px;">
                                    <td></td>
                                    <td style="color: #777; padding-left: 40px;">- ${idxName}</td>
                                    <td style="color: #777;">${dateStr}</td>

                                    <td style="color: #60a5fa;">-</td>
                                    <td style="color: #ff4d4d;">-</td>
                                    <td style="color: #999;">-</td>
                                    <td style="color: #bbb;">-</td>
                                    <td style="color: #ffeb3b;">${formatNum(subBuyC)}</td>
                                    <td style="color: #ffeb3b;">${formatNum(subSellC)}</td>
                                    <td style="color: ${getColor(subNetC)}; border-right: 1px solid #444;">${formatNum(subNetC)}</td>

                                    <td colspan="12" style="color: #555; text-align: center;">Not available</td>
                                </tr>
                            `;
                        }
                    });
                }
            }
        }
        blockHTML += `</tbody>`;
        document.getElementById('fii-smart-money-history-table').insertAdjacentHTML('beforeend', blockHTML);
    });
}
