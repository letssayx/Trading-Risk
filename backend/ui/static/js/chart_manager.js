// Chart Manager to interface with LightweightCharts
const ChartManager = {
    chart: null,
    candleSeries: null,
    container: null,

    init: function(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.chart = LightweightCharts.createChart(this.container, {
            width: this.container.clientWidth,
            height: this.container.clientHeight,
            layout: {
                backgroundColor: '#1e1e1e',
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: '#2B2B43' },
                horzLines: { color: '#2B2B43' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            timeScale: {
                borderColor: '#485c7b',
            },
        });

        this.candleSeries = this.chart.addCandlestickSeries({
            upColor: '#4caf50',
            downColor: '#f44336',
            borderVisible: false,
            wickUpColor: '#4caf50',
            wickDownColor: '#f44336',
        });

        // Handle resize
        window.addEventListener('resize', () => {
            this.chart.resize(this.container.clientWidth, this.container.clientHeight);
        });
    },

    loadData: async function(symbol) {
        if (!symbol) return;

        // Show loading state?
        console.log("Loading chart for", symbol);

        try {
            const res = await fetch(`/api/historical/${symbol}`);
            const data = await res.json();

            if (!Array.isArray(data)) {
                console.error("Invalid data format for chart");
                return;
            }

            // Format for Lightweight Charts: { time: 'yyyy-mm-dd', open, high, low, close }
            const chartData = data.map(d => ({
                time: d.time,
                open: d.open,
                high: d.high,
                low: d.low,
                close: d.close
            }));

            // Sort by time ascending just in case
            chartData.sort((a, b) => (new Date(a.time) - new Date(b.time)));

            this.candleSeries.setData(chartData);
            this.chart.timeScale().fitContent();

        } catch (e) {
            console.error("Chart load error:", e);
        }
    }
};
