
async function loadOptionsAnalysis() {
    const symbol = document.getElementById('opt-analysis-symbol').value.toUpperCase();
    if (!symbol) return;

    const loadBtn = document.getElementById('btn-load-options-analysis');
    let originalText = '';
    if (loadBtn) {
        originalText = loadBtn.innerHTML;
        loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        loadBtn.disabled = true;
    }

    // 1. Load 500-Day PCR Chart
    try {
        const days = document.getElementById('opt-analysis-lookback')?.value || '500';
        const showExpiryOnly = document.getElementById('pcr-expiry-only')?.checked || false;

        let url = `/api/data/derivatives/pcr_history?symbol=${symbol}&days=${days}&expiry_only=${showExpiryOnly}`;
        const res = await fetch(url);
        let data = await res.json();

        const chartDom = document.getElementById('opt-analysis-pcr-chart');
        if (pcrChartInstance) pcrChartInstance.dispose();
        pcrChartInstance = echarts.init(chartDom);

        const oiColors = data.total_oi.map((val, idx) => {
            if (idx === 0) return '#60a5fa';
            return val > data.total_oi[idx - 1] ? '#E88B1E' : '#60a5fa'; // Orange for up, Blue for down
        });

        // Calculate OI Change percentages
        const oiChangePct = data.total_oi.map((val, idx) => {
            if (idx === 0 || !data.total_oi[idx-1]) return 0;
            return ((val - data.total_oi[idx - 1]) / data.total_oi[idx - 1]) * 100;
        });

        // Calculate Price Change percentages
        const priceChangePct = data.price.map((val, idx) => {
            if (idx === 0 || !data.price[idx-1]) return 0;
            return ((val - data.price[idx - 1]) / data.price[idx - 1]) * 100;
        });

        const option = {
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
            legend: { data: ['Price (FUT1)', 'Total OI', 'OI Change %', 'PCR'], textStyle: { color: '#ccc' }, top: 0 },
            grid: [
                { left: '12%', right: '8%', top: '10%', height: '35%' },   // Top pane: Price
                { left: '12%', right: '8%', top: '48%', height: '22%' },   // Middle pane: OI
                { left: '12%', right: '8%', top: '72%', height: '15%' }    // Bottom pane: PCR
            ],
            axisPointer: { link: { xAxisIndex: 'all' }, label: { backgroundColor: '#777' } },
            xAxis: [
                {
                    type: 'category',
                    data: data.dates,
                    gridIndex: 0,
                    axisLabel: { show: false },
                    axisLine: { lineStyle: { color: '#333' } }
                },
                {
                    type: 'category',
                    data: data.dates,
                    gridIndex: 1,
                    axisLabel: { show: false },
                    axisLine: { lineStyle: { color: '#333' } }
                },
                {
                    type: 'category',
                    data: data.dates,
                    gridIndex: 2,
                    axisLabel: { color: '#888' },
                    axisLine: { lineStyle: { color: '#333' } }
                }
            ],
            yAxis: [
                {
                    type: 'value',
                    name: 'Price (FUT1)',
                    position: 'left',
                    gridIndex: 0,
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' },
                    scale: true,
                    min: function(value) { return Math.floor(value.min * 0.95); },
                            max: function(value) { return Math.ceil(value.max * 1.05); }
                },
                {
                    type: 'value',
                    name: 'Total OI',
                    position: 'left',
                    gridIndex: 1,
                    splitLine: { show: false },
                    axisLabel: { color: '#888', formatter: (value) => (value/1000000).toFixed(1) + 'M' },
                    nameTextStyle: { color: '#888' },
                    scale: true,
                    min: function(value) { return Math.floor(value.min * 0.95); },
                            max: function(value) { return Math.ceil(value.max * 1.05); }
                },
                {
                    type: 'value',
                    name: 'OI/Price Chg %',
                    position: 'right',
                    gridIndex: 1,
                    scale: true,
                    axisLabel: { color: '#888', formatter: '{value}%' },
                    splitLine: { show: false },
                    nameTextStyle: { color: '#888' }
                },
                {
                    type: 'value',
                    name: 'PCR',
                    position: 'left',
                    gridIndex: 2,
                    scale: true,
                    min: function(value) { return Math.floor(value.min * 0.95); },
                            max: function(value) { return Math.ceil(value.max * 1.05); },
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' }
                }
            ],
            dataZoom: [
                { type: 'inside', xAxisIndex: [0, 1, 2], start: 50, end: 100 },
                { type: 'slider', xAxisIndex: [0, 1, 2], start: 50, end: 100, textStyle: { color: '#ccc' }, bottom: '2%' }
            ],
            series: [
                {
                    name: 'Price (FUT1)',
                    type: 'line',
                    data: data.price,
                    itemStyle: { color: '#FFCC00' },
                    lineStyle: { width: 2 },
                    symbol: 'none',
                    xAxisIndex: 0,
                    yAxisIndex: 0
                },
                {
                    name: 'Total OI',
                    type: 'bar',
                    data: data.total_oi,
                    itemStyle: { color: (params) => oiColors[params.dataIndex] },
                    xAxisIndex: 1,
                    yAxisIndex: 1
                },
                {
                    name: 'OI Change %',
                    type: 'bar',
                    data: oiChangePct,
                    itemStyle: {
                        color: (params) => params.value >= 0 ? '#60a5fa' : '#f44336'
                    },
                    xAxisIndex: 1,
                    yAxisIndex: 2, // Secondary Y axis for percentages
                    barGap: '0%',
                    label: {
                        show: true,
                        position: 'top',
                        formatter: (params) => {
                            const pChg = priceChangePct[params.dataIndex];
                            return pChg ? pChg.toFixed(1) + '%' : '';
                        },
                        color: '#fff',
                        fontSize: 10,
                        backgroundColor: 'rgba(0,0,0,0.5)',
                        padding: 2,
                        borderRadius: 2
                    }
                },
                {
                    name: 'PCR',
                    type: 'line',
                    data: data.pcr,
                    itemStyle: { color: '#60a5fa' },
                    lineStyle: { width: 2 },
                    symbol: 'none',
                    xAxisIndex: 2,
                    yAxisIndex: 2
                }
            ]
        };
        pcrChartInstance.setOption(option);

        // Render 10-day history table below the chart
        const tbody = document.getElementById('opt-analysis-history-body');
        if (tbody) {
            tbody.innerHTML = '';
            if (data.dates && data.dates.length > 0) {
                const latestDataPoints = Math.min(10, data.dates.length);
                const startIdx = data.dates.length - latestDataPoints;

                for (let i = data.dates.length - 1; i >= startIdx; i--) {
                    const tr = document.createElement('tr');
                    const d = data.dates[i];
                    const p = data.price[i];
                    const oi = data.total_oi[i];
                    const pcr = data.pcr[i];
                    const pChg = priceChangePct[i];
                    const oiChg = oiChangePct[i];
                    const iv = data.atm_iv ? data.atm_iv[i] : 0;

                    let pColor = pChg >= 0 ? '#60a5fa' : '#f44336';
                    let oColor = oiChg >= 0 ? '#60a5fa' : '#f44336';

                    tr.innerHTML = `
                        <td style="padding: 6px;">${d}</td>
                        <td style="padding: 6px;">${p !== undefined && p !== null ? p.toFixed(2) : '-'}</td>
                        <td style="padding: 6px; color: ${pColor};">${pChg !== undefined && pChg !== null ? pChg.toFixed(2) + '%' : '-'}</td>
                        <td style="padding: 6px;">${oi !== undefined && oi !== null ? oi.toLocaleString() : '-'}</td>
                        <td style="padding: 6px; color: ${oColor};">${oiChg !== undefined && oiChg !== null ? oiChg.toFixed(2) + '%' : '-'}</td>
                        <td style="padding: 6px;">${pcr !== undefined && pcr !== null ? pcr.toFixed(2) : '-'}</td>
                        <td style="padding: 6px;">${iv ? iv.toFixed(2) + '%' : '-'}</td>
                    `;
                    tbody.appendChild(tr);
                }
            } else {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#888;">No historical data available.</td></tr>';
            }
        }
    } catch (e) {
        console.error("Error loading PCR history:", e);
    } finally {
        if (loadBtn) {
            loadBtn.innerHTML = originalText;
            loadBtn.disabled = false;
        }
    }

    // 2. Load High OI Chart
    try {
        const res = await fetch(`/api/data/derivatives/option_chain?symbol=${symbol}`);
        const data = await res.json();

        const chartDom = document.getElementById('opt-analysis-high-oi-chart');

        if (!data || !data.data || data.data.length === 0) {
            chartDom.innerHTML = '<p style="text-align:center; color:#888;">No Option Chain data found.</p>';
            return;
        }

        const strikes = [];
        const ce_oi = [];
        const pe_oi = [];

        // Instead of taking rigid +/- 20 strikes (which includes illiquid intermediate strikes),
        // we take the top 15 by Call OI and top 15 by Put OI, and union them.
        const allData = [...data.data];

        // Sort by CE OI descending
        const topCe = [...allData].sort((a, b) => (b.CE.oi || 0) - (a.CE.oi || 0)).slice(0, 15);
        // Sort by PE OI descending
        const topPe = [...allData].sort((a, b) => (b.PE.oi || 0) - (a.PE.oi || 0)).slice(0, 15);

        // Union the strikes using a Set to avoid duplicates
        const topStrikesSet = new Set();
        topCe.forEach(row => topStrikesSet.add(row.strike));
        topPe.forEach(row => topStrikesSet.add(row.strike));

        // Filter the original data to only include these top strikes, then sort by strike price
        const filteredData = allData
            .filter(row => topStrikesSet.has(row.strike))
            .sort((a, b) => a.strike - b.strike);

        filteredData.forEach(row => {
            strikes.push(row.strike);
            // CE OI mapped as negative to extend to the left of the axis
            ce_oi.push(row.CE.oi ? -row.CE.oi : 0);
            pe_oi.push(row.PE.oi || 0);
        });

        if (highOiChartInstance) highOiChartInstance.dispose();
        highOiChartInstance = echarts.init(chartDom);

        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' },
                formatter: function (params) {
                    let res = `<div style="font-weight:bold;">Strike: ${params[0].axisValue}</div>`;
                    params.forEach(function (p) {
                        const val = Math.abs(p.value).toLocaleString();
                        res += `<div style="color:${p.color};">${p.seriesName}: ${val}</div>`;
                    });
                    return res;
                }
            },
            legend: {
                data: ['Call OI', 'Put OI'],
                textStyle: { color: '#ccc' }
            },
            grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
            xAxis: {
                type: 'value',
                axisLabel: {
                    color: '#888',
                    formatter: function (value) { return Math.abs(value); }
                },
                splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
            },
            yAxis: {
                type: 'category',
                data: strikes,
                axisLabel: { color: '#FFCC00', fontWeight: 'bold' },
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { show: true, lineStyle: { color: '#222' } }
            },
            series: [
                {
                    name: 'Call OI',
                    type: 'bar',
                    stack: 'Total',
                    label: { show: false },
                    itemStyle: { color: '#3176B8' }, // Blue
                    data: ce_oi
                },
                {
                    name: 'Put OI',
                    type: 'bar',
                    stack: 'Total',
                    label: { show: false },
                    itemStyle: { color: '#E88B1E' }, // Orange
                    data: pe_oi
                }
            ]
        };

        highOiChartInstance.setOption(option);
    } catch (e) {
        console.error("Error loading high OI chart:", e);
    }

    if (loadBtn) {
        loadBtn.disabled = false;
        loadBtn.innerHTML = originalText;
    }
}
