window.ChartTabs = {
    tabs: [], // { id, symbol, container, chart, series, type, lastCandle }
    activeTabId: null,
    nextId: 1,

    init: function() {
        // Init Input
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

        // Add a default tab
        this.addTab('NIFTY');
    },

    addTab: async function(symbol, type='stock', params={}) {
        const id = this.nextId++;
        const containerId = `chart-instance-${id}`;

        // 1. Create Tab UI
        const tabEl = document.createElement('div');
        tabEl.className = 'chart-tab';
        tabEl.id = `tab-${id}`;
        tabEl.innerHTML = `<span>${symbol}</span> <span class="chart-tab-close" onclick="ChartTabs.closeTab(${id}, event)">×</span>`;
        tabEl.onclick = () => this.switchTab(id);

        // Insert before the input container (last element)
        const tabsBar = document.getElementById('chart-tabs-bar');
        const inputContainer = document.querySelector('.inline-add-container');
        tabsBar.insertBefore(tabEl, inputContainer);

        // 2. Create Chart Container
        const chartsContainer = document.getElementById('charts-container');
        const chartDiv = document.createElement('div');
        chartDiv.id = containerId;
        chartDiv.className = 'chart-instance';
        chartsContainer.appendChild(chartDiv);

        // 3. Init Lightweight Chart
        const chart = LightweightCharts.createChart(chartDiv, {
            width: chartDiv.clientWidth,
            height: chartDiv.clientHeight,
            layout: { background: { type: 'solid', color: '#131722' }, textColor: '#d1d4dc' },
            grid: { vertLines: { color: '#404040' }, horzLines: { color: '#404040' } },
            rightPriceScale: { borderColor: '#485c7b' },
            timeScale: { borderColor: '#485c7b' },
        });

        // Add Series (Candlestick for stock, Line for spread maybe?)
        let series;
        if (type === 'spread') {
            series = chart.addLineSeries({ color: '#2962FF', lineWidth: 2 });
        } else {
            series = chart.addCandlestickSeries({
                upColor: '#4caf50', downColor: '#f44336', borderVisible: false, wickUpColor: '#4caf50', wickDownColor: '#f44336'
            });
        }

        let lastCandle = null;

        // 4. Fetch Data
        try {
            let data;
            if (type === 'spread') {
                const res = await fetch(`/api/spread/historical?symbol1=${params.symbol1}&symbol2=${params.symbol2}&ratio=${params.ratio}`);
                data = await res.json();
            } else {
                const res = await fetch(`/api/historical/${symbol}`);
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                data = await res.json();
            }

            if (!Array.isArray(data)) {
                 console.error("Chart data is not an array:", data);
                 return;
            }

            // Format data for lightweight-charts
            data.sort((a,b) => new Date(a.time) - new Date(b.time));
            series.setData(data);

            if (data.length > 0) {
                lastCandle = data[data.length - 1];
            }

        } catch (e) {
            console.error("Failed to load chart data", e);
            // Show error in chart container
            const errDiv = document.createElement('div');
            errDiv.style.color = 'red';
            errDiv.style.padding = '20px';
            errDiv.innerText = "Error loading data: " + e.message;
            chartDiv.appendChild(errDiv);
        }

        // Store state
        this.tabs.push({ id, symbol, container: chartDiv, chart, series, type, lastCandle });

        // Subscribe to WS (global connection handles subscription)
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

            // Remove DOM
            document.getElementById(`tab-${id}`).remove();
            tab.container.remove();

            this.tabs.splice(index, 1);

            // Switch to another tab if active was closed
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

        // Update Tabs UI
        document.querySelectorAll('.chart-tab').forEach(t => t.classList.remove('active'));
        const activeTabEl = document.getElementById(`tab-${id}`);
        if(activeTabEl) activeTabEl.classList.add('active');

        // Update Containers
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
        // Find tabs monitoring this symbol
        this.tabs.forEach(t => {
            if (t.symbol === tick.symbol) {
                if (t.type === 'stock') {
                    // Update candle
                    // We assume tick.timestamp is ISO string
                    const tickDate = tick.timestamp.split('T')[0];
                    const price = tick.price;

                    let candle = t.lastCandle;
                    if (!candle) return;

                    // If same day, update existing candle
                    if (candle.time === tickDate) {
                        candle.close = price;
                        candle.high = Math.max(candle.high, price);
                        candle.low = Math.min(candle.low, price);
                    } else {
                        // New day, create new candle
                        candle = {
                            time: tickDate,
                            open: price,
                            high: price,
                            low: price,
                            close: price
                        };
                    }

                    // Update series
                    t.series.update(candle);
                    t.lastCandle = candle;
                } else if (t.type === 'spread') {
                    // Update line
                    const tickDate = tick.timestamp.split('T')[0];
                    t.series.update({ time: tickDate, value: tick.price });
                }
            }
        });
    }
};
