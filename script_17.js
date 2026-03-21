
    let echartInstance = null;
    let fiiDiiChartInstance = null;
    let participantChartInstance = null;

    async function loadMarketActivity() {
        const symbol = document.getElementById('market-activity-symbol').value.toUpperCase() || 'NIFTY';

        // 1. Load FII/DII Chart
        try {
            const res = await fetch('/api/market-activity/cash-flow');
            const data = await res.json();
            if (fiiDiiChartInstance) fiiDiiChartInstance.destroy();
            const ctx = document.getElementById('fiiDiiChart').getContext('2d');
            fiiDiiChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.dates,
                    datasets: [
                        { label: 'FII Net', data: data.fii_net, backgroundColor: 'rgba(54, 162, 235, 0.6)', borderColor: 'rgba(54, 162, 235, 1)', borderWidth: 1 },
                        { label: 'DII Net', data: data.dii_net, backgroundColor: 'rgba(255, 99, 132, 0.6)', borderColor: 'rgba(255, 99, 132, 1)', borderWidth: 1 }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: { x: { stacked: true }, y: { stacked: true } },
                    plugins: { legend: { labels: { color: '#ccc' } } }
                }
            });
        } catch (e) { console.error("Error loading FII/DII", e); }

        // 2. Load Participant OI Chart
        try {
            const res = await fetch('/api/market-activity/participant-oi');
            const data = await res.json();
            if (participantChartInstance) participantChartInstance.destroy();
            const ctx = document.getElementById('participantOiChart').getContext('2d');
            participantChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [
                        { label: 'FII Net Long', data: data.fii_net_long, borderColor: '#36a2eb', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'PRO Net Long', data: data.pro_net_long, borderColor: '#ffce56', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'Client Net Long', data: data.client_net_long, borderColor: '#4bc0c0', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    scales: { y: { grid: { color: '#333' } }, x: { grid: { display: false } } },
                    plugins: { legend: { labels: { color: '#ccc' } } }
                }
            });
        } catch (e) { console.error("Error loading Participant OI", e); }

        // 3. Load EChart Multi-Axis
        const container = document.getElementById('echart-container');
        if (!echartInstance) {
            echartInstance = echarts.init(container, 'dark', { renderer: 'canvas' });
        }

        echartInstance.showLoading({ text: 'Loading Data...', color: '#4ade80', textColor: '#fff', maskColor: 'rgba(30, 30, 30, 0.8)' });

        try {
            const res = await fetch(`/api/market-activity/dynamic-chart/${symbol}`);
            if (!res.ok) throw new Error("Data fetch failed");
            const data = await res.json();

            const option = {
                backgroundColor: 'transparent',
                tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                legend: { data: ['K-Line', 'MA20', 'Donchian Upper', 'Donchian Lower', 'Volume', 'ATR (14)', 'Future OI'] },
                grid: [
                    { left: '5%', right: '5%', height: '50%', top: '5%' }, // Main Chart
                    { left: '5%', right: '5%', top: '60%', height: '15%' }, // Volume
                    { left: '5%', right: '5%', top: '80%', height: '15%' }  // ATR / OI
                ],
                xAxis: [
                    { type: 'category', data: data.dates, gridIndex: 0, show: false },
                    { type: 'category', data: data.dates, gridIndex: 1, show: false },
                    { type: 'category', data: data.dates, gridIndex: 2 }
                ],
                yAxis: [
                    { scale: true, gridIndex: 0, splitLine: { show: true, lineStyle: { color: '#333' } } },
                    { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { formatter: (v) => (v/1000000).toFixed(1) + 'M' } },
                    { scale: true, gridIndex: 2, name: 'ATR %', splitNumber: 2, position: 'left' },
                    { scale: true, gridIndex: 2, name: 'Total OI', splitNumber: 2, position: 'right', axisLabel: { formatter: (v) => (v/1000000).toFixed(1) + 'M' } }
                ],
                dataZoom: [{ type: 'inside', xAxisIndex: [0, 1, 2], start: 50, end: 100 }, { show: true, type: 'slider', xAxisIndex: [0, 1, 2], bottom: '0%' }],
                series: [
                    { name: 'K-Line', type: 'candlestick', data: data.ohlc, itemStyle: { color: '#ef5350', color0: '#26a69a', borderColor: '#ef5350', borderColor0: '#26a69a' } },
                    { name: 'MA20', type: 'line', data: data.ma20, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#fff' } },
                    { name: 'Donchian Upper', type: 'line', data: data.donchian_upper, step: 'end', showSymbol: false, lineStyle: { type: 'dashed', color: '#ffeb3b', width: 1 } },
                    { name: 'Donchian Lower', type: 'line', data: data.donchian_lower, step: 'end', showSymbol: false, lineStyle: { type: 'dashed', color: '#ffeb3b', width: 1 } },
                    { name: 'Volume', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: data.volume, itemStyle: { color: '#5470c6' } },
                    { name: 'ATR (14)', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: data.atr, showSymbol: false, lineStyle: { color: '#fac858' } },
                    { name: 'Future OI', type: 'line', xAxisIndex: 2, yAxisIndex: 3, data: data.oi, showSymbol: false, lineStyle: { color: '#ee6666' } }
                ]
            };

            echartInstance.setOption(option, true);
        } catch (e) {
            container.innerHTML = `<div style="color:red; text-align:center; padding-top: 200px;">Error: ${e.message}</div>`;
        } finally {
            echartInstance?.hideLoading();
        }
    }

    // Listen for resize
    window.addEventListener('resize', () => { if (echartInstance) echartInstance.resize(); });
