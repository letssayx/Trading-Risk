import re

with open('backend/ui/static/js/rolloverTool.js', 'r') as f:
    content = f.read()

# Update dynamic chart logic to use solid bloomberg colors and fix resizing
dynamic_chart_func = """
    updateDynamicChart: async function() {
        const sectorEl = document.getElementById('rollover-chart-sector-filter');
        const stockSelect = document.getElementById('rollover-chart-stock-filter');
        const container = document.getElementById('rollover-dynamic-chart');

        if (!sectorEl || !stockSelect || !container) return;
        const sector = sectorEl.value;
        if (!sector) return;

        if (sector === 'ALL' || (!stockSelect.value && sector !== 'ALL')) {
            stockSelect.style.display = sector === 'ALL' ? 'none' : 'inline-block';

            if (sector !== 'ALL') {
                const sectorStocks = this.allData.filter(d => d.sector === sector).map(d => d.symbol).sort();
                let opts = '<option value="">Select Stock</option>';
                sectorStocks.forEach(s => opts += `<option value="${s}">${s}</option>`);
                stockSelect.innerHTML = opts;
            }

            let xData = [];
            let yData = [];
            let title = '';

            if (sector === 'ALL') {
                const sectors = [...new Set(this.allData.filter(d=>d.sector && d.sector !== "Unknown").map(d => d.sector))].sort();
                xData = sectors;
                yData = sectors.map(sec => {
                    const stocks = this.allData.filter(d => d.sector === sec);
                    if(stocks.length===0) return 0;
                    const avg = stocks.reduce((sum, s) => sum + s.rollover_pct, 0) / stocks.length;
                    return avg;
                });
                title = 'Current Avg Rollover by Sector';
            } else {
                const stocks = this.allData.filter(d => d.sector === sector).sort((a,b) => b.rollover_pct - a.rollover_pct);
                xData = stocks.map(s => s.symbol);
                yData = stocks.map(s => s.rollover_pct);
                title = `Current Rollover: ${sector} Stocks`;
            }

            const trace = {
                x: xData,
                y: yData,
                type: 'bar',
                marker: { color: '#00bcd4' },
                text: yData.map(v => v.toFixed(1) + '%'),
                textposition: 'auto'
            };

            const layout = {
                title: { text: title, font: {size: 12, color: '#ccc'} },
                paper_bgcolor: '#222',
                plot_bgcolor: '#222',
                font: { color: '#ccc' },
                margin: { t: 30, b: 60, l: 40, r: 10 },
                xaxis: { tickangle: -45 },
                yaxis: { title: 'Rollover %' }
            };

            Plotly.newPlot(container, [trace], layout, {responsive: true});

        } else if (stockSelect.value) {
            const symbol = stockSelect.value;
            try {
                // To show 12-month rollover history for a stock, we need to fetch it
                // Currently, we just mock the fetch or rely on a backend endpoint.
                // We'll update the endpoint or gracefully handle missing data.
                const res = await fetch(`/api/data/analysis/rollover/history/${symbol}`);
                let data = [];
                if (res.ok) {
                    const json = await res.json();
                    data = json.data || [];
                }

                if (data.length === 0) {
                    container.innerHTML = '<div style="color:#888; text-align:center; margin-top:50px;">No 12-month history available</div>';
                    return;
                }

                const trace = {
                    x: data.map(d => d.date),
                    y: data.map(d => d.rollover_pct),
                    type: 'bar',
                    marker: { color: '#00bcd4' },
                    text: data.map(d => d.rollover_pct.toFixed(1) + '%'),
                    textposition: 'auto'
                };

                const layout = {
                    title: { text: `12-Month Rollover History: ${symbol}`, font: {size: 12, color: '#ccc'} },
                    paper_bgcolor: '#222',
                    plot_bgcolor: '#222',
                    font: { color: '#ccc' },
                    margin: { t: 30, b: 60, l: 40, r: 10 },
                    xaxis: { type: 'category' },
                    yaxis: { title: 'Rollover %' }
                };

                Plotly.newPlot(container, [trace], layout, {responsive: true});
            } catch(e) {
                console.error("Failed to load stock rollover history", e);
                container.innerHTML = '<div style="color:red; text-align:center; margin-top:50px;">Failed to load history</div>';
            }
        }
    },
"""

start_idx = content.find("updateDynamicChart: async function() {")
if start_idx != -1:
    end_idx = content.find("filterData: function() {", start_idx)
    content = content[:start_idx] + dynamic_chart_func + "\n    " + content[end_idx:]

    with open('backend/ui/static/js/rolloverTool.js', 'w') as f:
        f.write(content)
    print("Patched dynamic chart.")
else:
    print("Could not find updateDynamicChart.")
