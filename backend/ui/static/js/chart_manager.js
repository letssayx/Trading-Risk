// Chart Manager
// Handles multiple chart tabs and data loading

class ChartTabs {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.tabsContainer = document.createElement('div');
        this.tabsContainer.className = 'chart-tabs-bar';
        this.tabsContainer.style.cssText = "display:flex; background:#222; border-bottom:1px solid #444; height:30px;";

        this.contentContainer = document.createElement('div');
        this.contentContainer.style.cssText = "flex:1; position:relative;";

        this.container.innerHTML = '';
        this.container.appendChild(this.tabsContainer);
        this.container.appendChild(this.contentContainer);

        this.tabs = {}; // id -> { tabEl, contentEl, chartInstance, symbol }
        this.activeTabId = null;

        // Initial Tab
        this.addTab('NIFTY');
    }

    async addTab(symbol) {
        const id = 'chart_' + Date.now();

        // Tab UI
        const tabEl = document.createElement('div');
        tabEl.className = 'chart-tab';
        tabEl.style.cssText = "padding:6px 12px; cursor:pointer; color:#aaa; border-right:1px solid #333; font-size:0.8em; display:flex; align-items:center;";
        tabEl.innerHTML = `<span>${symbol}</span> <span style="margin-left:8px; font-weight:bold;" onclick="window.chartTabs.closeTab('${id}', event)">x</span>`;
        tabEl.onclick = () => this.switchTab(id);
        this.tabsContainer.appendChild(tabEl);

        // Chart Container
        const contentEl = document.createElement('div');
        contentEl.style.cssText = "width:100%; height:100%; position:absolute; top:0; left:0; display:none;";
        this.contentContainer.appendChild(contentEl);

        // Init Chart
        const chart = LightweightCharts.createChart(contentEl, {
            layout: { background: { type: 'solid', color: '#1A1B20' }, textColor: '#ccc' },
            grid: { vertLines: { color: '#333' }, horzLines: { color: '#333' } },
            timeScale: { borderColor: '#444' },
            rightPriceScale: { borderColor: '#444' },
        });
        const series = chart.addCandlestickSeries({
            upColor: '#4caf50', downColor: '#f44336', borderVisible: false, wickUpColor: '#4caf50', wickDownColor: '#f44336'
        });

        // Load Data
        const data = await this.fetchHistory(symbol);
        series.setData(data);

        this.tabs[id] = { tabEl, contentEl, chart, series, symbol };
        this.switchTab(id);
    }

    async fetchHistory(symbol) {
        try {
            const res = await fetch(`/api/historical/${symbol}`);
            return await res.json();
        } catch(e) {
            console.error(e);
            return [];
        }
    }

    switchTab(id) {
        if (this.activeTabId) {
            this.tabs[this.activeTabId].contentEl.style.display = 'none';
            this.tabs[this.activeTabId].tabEl.style.background = 'transparent';
            this.tabs[this.activeTabId].tabEl.style.color = '#aaa';
        }

        this.activeTabId = id;
        this.tabs[id].contentEl.style.display = 'block';
        this.tabs[id].tabEl.style.background = '#1A1B20';
        this.tabs[id].tabEl.style.color = '#fff';

        // Trigger resize
        const { width, height } = this.contentContainer.getBoundingClientRect();
        this.tabs[id].chart.applyOptions({ width, height });
    }

    closeTab(id, e) {
        e.stopPropagation();
        const tab = this.tabs[id];
        tab.tabEl.remove();
        tab.contentEl.remove();
        delete this.tabs[id];

        if (this.activeTabId === id) {
            const remaining = Object.keys(this.tabs);
            if (remaining.length > 0) this.switchTab(remaining[remaining.length-1]);
            else this.activeTabId = null;
        }
    }

    updateTick(symbol, price) {
        // Find tabs for this symbol
        Object.values(this.tabs).forEach(tab => {
            if (tab.symbol === symbol) {
                // Update last candle (Simplistic)
                // In real app, check timestamps etc.
                // We'll just update the close of the last bar for visual effect
                // or create a new bar if needed.
                // For MVP, assume the series data structure matches
            }
        });
    }
}

// Global Access
window.ChartTabs = ChartTabs;
document.addEventListener('DOMContentLoaded', () => {
    window.chartTabs = new ChartTabs('chart-panel');
});
