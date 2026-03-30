let pcrChartInstance = null;
let highOiChartInstance = null;

async function loadOptionsAnalysis() {
    const symbol = document.getElementById('opt-analysis-symbol').value.toUpperCase();
    if (!symbol) return;

    // 1. Load 500-Day PCR Chart
    try {
        const days = document.getElementById('opt-analysis-lookback')?.value || '500';
        const res = await fetch(`/api/data/derivatives/pcr_history?symbol=${symbol}&days=${days}`);
        const data = await res.json();

        const chartDom = document.getElementById('opt-analysis-pcr-chart');
        if (pcrChartInstance) pcrChartInstance.dispose();
        pcrChartInstance = echarts.init(chartDom);

        const option = {
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
            legend: { data: ['Total OI', 'Price (FUT1)', 'PCR'], textStyle: { color: '#ccc' } },
            grid: { left: '3%', right: '3%', bottom: '3%', top: '15%', containLabel: true },
            xAxis: {
                type: 'category',
                data: data.dates,
                axisLabel: { color: '#888' },
                axisLine: { lineStyle: { color: '#333' } }
            },
            yAxis: [
                {
                    type: 'value',
                    name: 'Total OI',
                    position: 'left',
                    splitLine: { show: false },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' }
                },
                {
                    type: 'value',
                    name: 'Price (FUT1)',
                    position: 'right',
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' },
                    scale: true,
                    min: 'dataMin',
                    max: 'dataMax'
                },
                {
                    type: 'value',
                    name: 'PCR',
                    position: 'right',
                    offset: 60,
                    scale: true,
                    min: 'dataMin',
                    max: 'dataMax',
                    splitLine: { show: false },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' }
                }
            ],
            dataZoom: [
                { type: 'inside', start: 50, end: 100 },
                { type: 'slider', start: 50, end: 100, textStyle: { color: '#ccc' } }
            ],
            series: [
                {
                    name: 'Total OI',
                    type: 'bar',
                    data: data.total_oi,
                    itemStyle: { color: 'rgba(54, 162, 235, 0.4)' },
                    yAxisIndex: 0
                },
                {
                    name: 'Price (FUT1)',
                    type: 'line',
                    data: data.price,
                    itemStyle: { color: '#FFCC00' },
                    lineStyle: { width: 2 },
                    symbol: 'none',
                    yAxisIndex: 1
                },
                {
                    name: 'PCR',
                    type: 'line',
                    data: data.pcr,
                    itemStyle: { color: '#00FF00' },
                    lineStyle: { width: 2 },
                    symbol: 'none',
                    yAxisIndex: 2
                }
            ]
        };
        pcrChartInstance.setOption(option);
    } catch (e) {
        console.error("Error loading PCR history:", e);
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

        // Take ATM +/- 20 strikes
        const sortedData = data.data.sort((a,b) => a.strike - b.strike);
        let atmIndex = 0;
        let minDiff = Infinity;

        for (let i = 0; i < sortedData.length; i++) {
            const diff = Math.abs(sortedData[i].strike - data.spot_price);
            if (diff < minDiff) {
                minDiff = diff;
                atmIndex = i;
            }
        }

        const startIdx = Math.max(0, atmIndex - 20);
        const endIdx = Math.min(sortedData.length, atmIndex + 20);
        const filteredData = sortedData.slice(startIdx, endIdx);

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
}
