
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
        if (!data || !data.dates || data.dates.length === 0) {
            chartDom.innerHTML = '<p style="text-align:center; color:#888;">No historical data found.</p>';
            return;

        }
        if (window.pcrChartInstance) window.pcrChartInstance.dispose();
        window.pcrChartInstance = echarts.init(chartDom);

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
                { left: '5%', right: '50%', bottom: '5%', top: '10%' },
                { left: '50%', right: '5%', bottom: '5%', top: '10%' }
            ],
            xAxis: [
                {
                    type: 'value',
                    gridIndex: 0,
                    inverse: true,
                    axisLabel: { color: '#888', formatter: (value) => Math.abs(value).toLocaleString() },
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
                },
                {
                    type: 'value',
                    gridIndex: 1,
                    axisLabel: { color: '#888', formatter: (value) => Math.abs(value).toLocaleString() },
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
                }
            ],
            yAxis: [
                {
                    type: 'category',
                    gridIndex: 0,
                    data: strikes,
                    position: 'right',
                    axisLabel: { show: true, color: '#FFCC00', fontWeight: 'bold', margin: 15, align: 'center' },
                    axisLine: { show: false },
                    axisTick: { show: false }
                },
                {
                    type: 'category',
                    gridIndex: 1,
                    data: strikes,
                    position: 'left',
                    axisLabel: { show: false },
                    axisLine: { show: false },
                    axisTick: { show: false }
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
                    yAxisIndex: 3
                }
            ]
        };
        window.pcrChartInstance.setOption(option);
        setTimeout(() => window.pcrChartInstance.resize(), 100);
    } catch (e) {
        console.error("Error loading PCR history:", e);
    }

    // 2. Load High OI Chart
    try {
        const res = await fetch(`/api/data/derivatives/option_chain?symbol=${symbol}`);
        const data = await res.json();

        const chartDom = document.getElementById('opt-analysis-high-oi-chart');

        if (data.error || !data || !data.data || data.data.length === 0) {
            console.error('API Error:', data.error || 'No Option Chain data found.');
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
            .sort((a, b) => b.strike - a.strike);

        filteredData.forEach(row => {
            strikes.push(row.strike);
            // CE OI mapped as negative to extend to the left of the axis
            ce_oi.push(row.CE.oi ? -row.CE.oi : 0);
            pe_oi.push(row.PE.oi || 0);
        });

        if (window.highOiChartInstance) window.highOiChartInstance.dispose();
        window.highOiChartInstance = echarts.init(chartDom);

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
                        grid: [
                { left: '5%', right: '50%', bottom: '5%', top: '10%' },
                { left: '50%', right: '5%', bottom: '5%', top: '10%' }
            ],
            xAxis: [
                {
                    type: 'value',
                    gridIndex: 0,
                    inverse: true,
                    axisLabel: { color: '#888', formatter: (value) => Math.abs(value).toLocaleString() },
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
                },
                {
                    type: 'value',
                    gridIndex: 1,
                    axisLabel: { color: '#888', formatter: (value) => Math.abs(value).toLocaleString() },
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
                }
            ],
            yAxis: [
                {
                    type: 'category',
                    gridIndex: 0,
                    data: strikes,
                    position: 'right',
                    axisLabel: { show: true, color: '#FFCC00', fontWeight: 'bold', margin: 15, align: 'center' },
                    axisLine: { show: false },
                    axisTick: { show: false }
                },
                {
                    type: 'category',
                    gridIndex: 1,
                    data: strikes,
                    position: 'left',
                    axisLabel: { show: false },
                    axisLine: { show: false },
                    axisTick: { show: false }
                }
            ],
            series: [
                {
                    name: 'Call OI',
                    type: 'bar',
                    xAxisIndex: 0,
                    yAxisIndex: 0,
                    label: { show: false },
                    itemStyle: { color: '#E88B1E' }, // Orange for Calls
                    data: ce_oi.map(v => Math.abs(v)) // Pass absolute, axis inversion handles visualization
                },
                {
                    name: 'Put OI',
                    type: 'bar',
                    xAxisIndex: 1,
                    yAxisIndex: 1,
                    label: { show: false },
                    itemStyle: { color: '#3176B8' }, // Blue for Puts
                    data: pe_oi
                }
            ]
        };

        window.highOiChartInstance.setOption(option);
        setTimeout(() => window.highOiChartInstance.resize(), 100);
    } catch (e) {
        console.error("Error loading high OI chart:", e);
    }

    if (loadBtn) {
        loadBtn.disabled = false;
        loadBtn.innerHTML = originalText;
    }
}

window.addEventListener('resize', function () {
    if (typeof window.pcrChartInstance !== 'undefined' && window.pcrChartInstance) {
        window.pcrChartInstance.resize();
    }
    if (typeof window.highOiChartInstance !== 'undefined' && window.highOiChartInstance) {
        window.highOiChartInstance.resize();
    }
});
