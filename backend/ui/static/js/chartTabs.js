window.ChartTabs = {
    tabs: [], // { id, symbol, container, chart, series, type, lastCandle }
    activeTabId: null,
    nextId: 1,

    init: function() {
        const input = document.getElementById('chart-add-input');
        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const val = e.target.value.trim().toUpperCase();
                    if (val) {
                        this.addTab(val);
                        e.target.value = '';
                    }
                }
            });
        }
        this.addTab('NIFTY');
    },

    addTab: async function(symbol, type='stock', segment='CM') {
        const id = this.nextId++;
        const containerId = `chart-instance-${id}`;

        const tabEl = document.createElement('div');
        tabEl.className = 'chart-tab';
        tabEl.id = `tab-${id}`;
        tabEl.innerHTML = `<span>${symbol} <small>(${segment})</small></span> <span class="chart-tab-close" onclick="ChartTabs.closeTab(${id}, event)">×</span>`;
        tabEl.onclick = () => this.switchTab(id);

        const tabsBar = document.getElementById('chart-tabs-bar');
        const inputContainer = document.querySelector('.inline-add-container');
        tabsBar.insertBefore(tabEl, inputContainer);

        const chartsContainer = document.getElementById('charts-container');
        const chartDiv = document.createElement('div');
        chartDiv.id = containerId;
        chartDiv.className = 'chart-instance';
        // Ensure visible for dimension calculation
        chartDiv.style.display = 'block';
        chartsContainer.appendChild(chartDiv);

        const chart = LightweightCharts.createChart(chartDiv, {
            width: chartDiv.clientWidth,
            height: chartDiv.clientHeight,
            layout: { background: { type: 'solid', color: '#131722' }, textColor: '#d1d4dc' },
            grid: { vertLines: { color: '#404040' }, horzLines: { color: '#404040' } },
            rightPriceScale: { borderColor: '#485c7b' },
            timeScale: { borderColor: '#485c7b' },
        });

        let series;
        if (type === 'spread') {
            series = chart.addLineSeries({ color: '#2962FF', lineWidth: 2 });
        } else {
            series = chart.addCandlestickSeries({
                upColor: '#4caf50', downColor: '#f44336', borderVisible: false, wickUpColor: '#4caf50', wickDownColor: '#f44336'
            });
        }

        let lastCandle = null;

        try {
            let data;
            if (type === 'spread') {
                // Spread not fully supported with segment yet, assume params passed elsewhere or handle separately
                // For now, minimal support
                const res = await fetch(`/api/spread/historical?symbol1=${symbol.split('-')[0]}&symbol2=${symbol.split('-')[1]}`);
                data = await res.json();
            } else {
                const res = await fetch(`/api/historical/${symbol}?segment=${segment}`);
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                data = await res.json();
            }

            if (!Array.isArray(data)) {
                 console.error("Chart data is not an array:", data);
                 data = [];
            }

            data.sort((a,b) => new Date(a.time) - new Date(b.time));
            series.setData(data);

            if (data.length > 0) {
                lastCandle = data[data.length - 1];
            }

        } catch (e) {
            console.error("Failed to load chart data", e);
            const errDiv = document.createElement('div');
            errDiv.style.color = 'red';
            errDiv.style.padding = '20px';
            errDiv.innerText = "Error loading data: " + e.message;
            chartDiv.appendChild(errDiv);
        }

        this.tabs.push({ id, symbol, container: chartDiv, chart, series, type, lastCandle });

        if (window.ws && window.ws.readyState === WebSocket.OPEN) {
            window.ws.send(JSON.stringify({ subscribe: [symbol] }));
        }

        this.switchTab(id);
    },

    closeTab: function(id, event) {
        event.stopPropagation();
        const index = this.tabs.findIndex(t => t.id === id);
        if (index > -1) {
            const tab = this.tabs[index];
            document.getElementById(`tab-${id}`).remove();
            tab.container.remove();
            this.tabs.splice(index, 1);
            if (this.activeTabId === id) {
                if (this.tabs.length > 0) {
                    this.switchTab(this.tabs[this.tabs.length - 1].id);
                } else {
                    this.activeTabId = null;
                }
            }
        }
    },

    switchTab: function(id) {
        this.activeTabId = id;
        document.querySelectorAll('.chart-tab').forEach(t => t.classList.remove('active'));
        const activeTabEl = document.getElementById(`tab-${id}`);
        if(activeTabEl) activeTabEl.classList.add('active');
        document.querySelectorAll('.chart-instance').forEach(c => c.style.display = 'none');
        const activeTab = this.tabs.find(t => t.id === id);
        if (activeTab) {
            activeTab.container.style.display = 'block';
            activeTab.chart.timeScale().fitContent();
        }
    },

    resizeAll: function() {
        this.tabs.forEach(t => {
            if (t.container) {
                t.chart.applyOptions({
                    width: t.container.clientWidth,
                    height: t.container.clientHeight
                });
            }
        });
    },

    handleTick: function(tick) {
        this.tabs.forEach(t => {
            if (t.symbol === tick.symbol) {
                // Update logic... simplified for brevity as user didn't request tick logic change
                // Assuming tick has proper structure
                 if (t.type === 'stock') {
                    const tickDate = tick.timestamp ? tick.timestamp.split('T')[0] : new Date().toISOString().split('T')[0];
                    const price = tick.price;
                    let candle = t.lastCandle;
                    if (!candle) return;
                    if (candle.time === tickDate) {
                        candle.close = price;
                        candle.high = Math.max(candle.high, price);
                        candle.low = Math.min(candle.low, price);
                    } else {
                        candle = { time: tickDate, open: price, high: price, low: price, close: price };
                    }
                    t.series.update(candle);
                    t.lastCandle = candle;
                }
            }
        });
    }
};
