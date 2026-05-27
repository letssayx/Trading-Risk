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
                    x: { ticks: { color: '#aaa' }, grid: { color: '#333' } },
                    y: { ticks: { color: '#aaa' }, grid: { color: '#333' } }
                }
            }
        });

        // Load FII Money Stats
        const moneyRes = await fetch(`/api/market-activity/participant-oi-money?days=${days}`);
        const moneyData = await moneyRes.json();

        const moneyChartDom = document.getElementById('fii-money-tab-daily-summary');
        if (window.fiiMoneyTabChartInstance) window.fiiMoneyTabChartInstance.dispose();
        window.fiiMoneyTabChartInstance = echarts.init(moneyChartDom);

        const seriesMoney = [];
        seriesMoney.push({
            name: 'FII Net (Cr)',
            type: 'bar',
            data: moneyData.fii_money,
            itemStyle: { color: (p) => p.value >= 0 ? '#60a5fa' : '#f44336' }
        });

        window.fiiMoneyTabChartInstance.setOption({
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis' },
            legend: { data: ['FII Net (Cr)'], textStyle: { color: '#ccc' } },
            grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
            xAxis: { type: 'category', data: moneyData.dates, axisLabel: { color: '#888' } },
            yAxis: { type: 'value', axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#333' } } },
            series: seriesMoney
        });

        // Load Participant Contracts
        const partRes = await fetch(`/api/market-activity/participant-oi?days=${days}`);
        const partData = await partRes.json();

        const partChartDom = document.getElementById('participant-oi-tab-daily-summary');
        if (window.participantTabChartInstance) window.participantTabChartInstance.dispose();
        window.participantTabChartInstance = echarts.init(partChartDom);

        // Calculate smart money
        const smartMoney = partData.dates.map((_, i) => (partData.fii[i] || 0) + (partData.dii[i] || 0) + (partData.pro[i] || 0));

        window.participantTabChartInstance.setOption({
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis' },
            legend: { data: ['Smart Money'], textStyle: { color: '#ccc' } },
            grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
            xAxis: { type: 'category', data: partData.dates, axisLabel: { color: '#888' } },
            yAxis: { type: 'value', axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#333' } } },
            series: [{ name: 'Smart Money', type: 'line', data: smartMoney, itemStyle: { color: '#9c27b0' }, areaStyle: {} }]
        });

        // Load Participant Granular
        const granChartDom = document.getElementById('participant-oi-tab-granular-summary');
        if (window.participantGranularTabChartInstance) window.participantGranularTabChartInstance.dispose();
        window.participantGranularTabChartInstance = echarts.init(granChartDom);

        const participants = [
            { key: 'fii', label: 'FII', color: '#3176B8' },
            { key: 'dii', label: 'DII', color: '#ff9800' },
            { key: 'pro', label: 'PRO', color: '#4caf50' },
            { key: 'client', label: 'Client', color: '#f44336' }
        ];

        const granSeries = participants.map(p => ({
            name: p.label,
            type: 'bar',
            stack: 'total',
            data: partData[p.key],
            itemStyle: { color: p.color }
        }));

        window.participantGranularTabChartInstance.setOption({
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
            legend: { data: participants.map(p => p.label), textStyle: { color: '#ccc' } },
            grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
            xAxis: { type: 'category', data: partData.dates, axisLabel: { color: '#888' } },
            yAxis: { type: 'value', axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#333' } } },
            series: granSeries
        });

    } catch (e) {
        console.error("Error loading FII Analysis", e);
    }
}
