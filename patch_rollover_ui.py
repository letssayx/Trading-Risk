import re

with open("backend/ui/static/js/rolloverTool.js", "r") as f:
    content = f.read()

# Update the render function HTML
new_render = """
    render: function(container) {
        container.innerHTML = `
            <style>
                .roll-row { border-bottom: 1px solid #333; }
                .roll-row:hover { background-color: #2a2a2a; cursor: pointer; }
                .roll-history-row { display: none; background-color: #1a1a1a; }
                .roll-history-row td { padding: 0 !important; border: none; }
                .roll-history-table { width: 100%; border-collapse: collapse; margin-left: 30px; font-size: 0.9em; color: #aaa; }
                .roll-history-table th, .roll-history-table td { padding: 6px 8px; border-bottom: 1px solid #222; text-align: left; }
                .roll-history-table th { background: #111; color: #888; }
            </style>
            <div style="color: #ccc; height: 100%; display: flex; flex-direction: column;">
                <div style="display: flex; gap: 15px; margin-bottom: 15px; align-items: center; flex-shrink: 0; flex-wrap: wrap;">
                    <h2 style="margin: 0; color: #fff; font-size: 18px;">Rollover Analysis</h2>
                    <input type="text" id="rollover-symbol" class="form-control history-input" placeholder="Search Symbol" style="width: 150px; padding: 4px;" oninput="RolloverTool.filterData()">
                    <select id="rollover-sector-filter" class="form-control history-input" style="width: 150px; padding: 4px;" onchange="RolloverTool.filterData()">
                        <option value="">All Sectors</option>
                    </select>
                    <button onclick="RolloverTool.loadAggregatedData()" class="btn btn-primary"><i class="fas fa-sync"></i> Refresh All</button>
                    <button onclick="RolloverTool.analyzeSingle()" class="btn btn-secondary">Load Single Details</button>
                    <button class="btn btn-secondary" onclick="exportTableToCSV('rollover-analysis-table', 'Rollover_Analysis')"><i class="fas fa-download"></i> CSV</button>
                    <span id="rollover-date-display" style="color: #888; margin-left: auto;"></span>
                </div>

                <div id="rollover-results" style="flex: 1; overflow: auto; display: flex; flex-direction: column; gap: 20px;">

                    <!-- Chart Area -->
                    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                        <div style="flex: 1; min-width: 400px; height: 300px; border: 1px solid #333; border-radius: 4px; background: #1e1e1e; padding: 10px; display: flex; flex-direction: column;">
                            <h4 style="margin: 0 0 10px 0; color: #ccc; font-size: 14px; border-bottom: 1px solid #333; padding-bottom: 5px;">Sectoral Rollover (Previous 2 Expiries)</h4>
                            <div id="rollover-sector-chart" style="flex: 1;"></div>
                        </div>
                        <div style="flex: 1; min-width: 400px; height: 300px; border: 1px solid #333; border-radius: 4px; background: #1e1e1e; padding: 10px; display: flex; flex-direction: column;">
                            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 10px;">
                                <h4 style="margin: 0; color: #ccc; font-size: 14px;">Historical Rollover</h4>
                                <select id="rollover-chart-sector-filter" class="form-control history-input" style="width: 130px; padding: 2px; font-size: 12px;" onchange="RolloverTool.updateDynamicChart()">
                                    <option value="ALL">All Sectors</option>
                                </select>
                                <select id="rollover-chart-stock-filter" class="form-control history-input" style="width: 130px; padding: 2px; font-size: 12px; display:none;" onchange="RolloverTool.updateDynamicChart()">
                                    <option value="">Select Stock</option>
                                </select>
                            </div>
                            <div id="rollover-dynamic-chart" style="flex: 1;"></div>
                        </div>
                    </div>

                    <!-- Table Area -->
                    <div class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow-x: auto; flex: 1;">
                        <table class="data-table" id="rollover-analysis-table" style="width: 100%;">
                            <thead style="position: sticky; top: 0; background: #222; z-index: 10;">
                                <tr>
                                    <th style="padding: 8px; width: 30px;"></th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('symbol')">Symbol ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('sector')">Sector ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_pct')">Rollover % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('oi_chg_pct')">OI Chg % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('price')">FUT Price ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('price_chg_pct')">Price Chg % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost')">Spread (Pts) ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost_pct')">Cost % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('near_oi')">Near OI ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('total_oi')">Total OI ↕</th>
                                </tr>
                            </thead>
                            <tbody id="rollover-analysis-body">
                                <tr><td colspan="11" style="text-align:center; color:#888;">Loading Rollover Data...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        const input = document.getElementById('rollover-symbol');
        if (input) {
            if (typeof setupAutocomplete === 'function') {
                setupAutocomplete('rollover-symbol');
            }
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    if (input.value.trim() === '') {
                        RolloverTool.loadAggregatedData();
                    } else {
                        RolloverTool.analyzeSingle();
                    }
                }
            });
            input.addEventListener('input', (e) => {
                if (input.value.trim() === '') {
                    RolloverTool.loadAggregatedData();
                } else {
                    if (document.getElementById('rollover-analysis-body')) {
                        RolloverTool.filterData();
                    }
                }
            });
        }
    },
"""
content = re.sub(r"render: function\(container\) \{[\s\S]*?(?=loadAggregatedData: async function\(\) \{)", new_render, content)

# Inject populate filters logic into loadAggregatedData
load_agg_injection = """            // Populate sector filters
            const sectors = new Set();
            this.allData.forEach(d => {
                if (d.sector && d.sector !== "Unknown") {
                    sectors.add(d.sector);
                }
            });
            const sectorSelect = document.getElementById('rollover-sector-filter');
            const chartSectorSelect = document.getElementById('rollover-chart-sector-filter');
            if (sectorSelect && chartSectorSelect) {
                const currentVal = sectorSelect.value;
                const cCurrentVal = chartSectorSelect.value;

                let opts = '<option value="">All Sectors</option>';
                let cOpts = '<option value="ALL">All Sectors</option>';

                Array.from(sectors).sort().forEach(s => {
                    opts += `<option value="${s}">${s}</option>`;
                    cOpts += `<option value="${s}">${s}</option>`;
                });

                sectorSelect.innerHTML = opts;
                sectorSelect.value = currentVal;

                chartSectorSelect.innerHTML = cOpts;
                if(cCurrentVal) chartSectorSelect.value = cCurrentVal;
            }

            this.renderAggregatedView();
            this.loadSectoralChart();
            this.updateDynamicChart();"""

content = content.replace("this.renderAggregatedView();", load_agg_injection)

# Add toggleHistory method
toggle_history = """
    toggleHistory: function(symbol) {
        const row = document.getElementById(`roll-history-${symbol}`);
        const icon = document.getElementById(`roll-icon-${symbol}`);
        if (row) {
            if (row.style.display === 'none' || row.style.display === '') {
                row.style.display = 'table-row';
                if (icon) icon.innerHTML = '▼';
            } else {
                row.style.display = 'none';
                if (icon) icon.innerHTML = '▶';
            }
        }
    },
"""
content = content.replace("renderAggregatedView: function() {", toggle_history + "    renderAggregatedView: function() {")

# Update renderAggregatedView table HTML
table_render_code = """
        // Render Table
        const tbody = document.getElementById('rollover-analysis-body');
        tbody.innerHTML = '';

        if (displayData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; color:#888;">No F&O stocks found.</td></tr>';
        } else {
            let html = '';
            displayData.forEach(d => {
                let costColor = d.rollover_cost >= 0 ? '#4caf50' : '#f44336';
                let rollColor = d.rollover_pct >= 80 ? '#00bcd4' : '#ccc';
                let oColor = d.oi_chg_pct >= 0 ? '#4caf50' : '#f44336';
                let pColor = d.price_chg_pct >= 0 ? '#4caf50' : '#f44336';

                let histHtml = '';
                if (d.history && d.history.length > 0) {
                    histHtml = `<table class="roll-history-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>FUT Price</th>
                                <th>Price Chg %</th>
                                <th>Total OI</th>
                                <th>OI Chg %</th>
                            </tr>
                        </thead>
                        <tbody>
                    `;
                    d.history.forEach(h => {
                        let hpColor = h.price_chg_pct >= 0 ? '#4caf50' : '#f44336';
                        let hoColor = h.oi_chg_pct >= 0 ? '#4caf50' : '#f44336';
                        histHtml += `<tr>
                            <td>${h.date}</td>
                            <td>${(h.price || 0).toFixed(2)}</td>
                            <td style="color: ${hpColor}">${(h.price_chg_pct || 0).toFixed(2)}%</td>
                            <td>${(h.oi || 0).toLocaleString()}</td>
                            <td style="color: ${hoColor}">${(h.oi_chg_pct || 0).toFixed(2)}%</td>
                        </tr>`;
                    });
                    histHtml += `</tbody></table>`;
                } else {
                    histHtml = `<div style="padding: 10px; color: #888; margin-left: 30px;">No historical data available</div>`;
                }

                html += `<tr class="roll-row" onclick="RolloverTool.toggleHistory('${d.symbol}')">
                    <td style="padding: 8px; text-align: center;"><span id="roll-icon-${d.symbol}" style="font-size: 10px;">▶</span></td>
                    <td style="padding: 8px;"><b>${d.symbol}</b></td>
                    <td style="padding: 8px; color: #aaa;">${d.sector || ''}</td>
                    <td style="padding: 8px; color: ${rollColor}; font-weight: bold;">${d.rollover_pct}%</td>
                    <td style="padding: 8px; color: ${oColor};">${(d.oi_chg_pct||0).toFixed(2)}%</td>
                    <td style="padding: 8px;">${(d.price||0).toFixed(2)}</td>
                    <td style="padding: 8px; color: ${pColor};">${(d.price_chg_pct||0).toFixed(2)}%</td>
                    <td style="padding: 8px; color: ${costColor};">${d.rollover_cost}</td>
                    <td style="padding: 8px; color: ${costColor};">${d.rollover_cost_pct}%</td>
                    <td style="padding: 8px; color: #888;">${d.near_oi}</td>
                    <td style="padding: 8px; color: #888;">${d.total_oi}</td>
                </tr>
                <tr id="roll-history-${d.symbol}" class="roll-history-row">
                    <td colspan="11">${histHtml}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
        }"""

content = re.sub(r"// Render Table[\s\S]*?tbody\.innerHTML = html;\n\s+\}", table_render_code, content)

# Add sectorFilter handling
content = content.replace("const symbolFilter = document.getElementById('rollover-symbol').value.toUpperCase().trim();", "const symbolFilter = document.getElementById('rollover-symbol').value.toUpperCase().trim();\n        const sectorFilter = document.getElementById('rollover-sector-filter').value;")
content = content.replace("if (symbolFilter) {", "if (sectorFilter) {\n            displayData = displayData.filter(d => d.sector === sectorFilter);\n        }\n\n        if (symbolFilter) {")


# Add new chart methods
new_methods = """
    loadSectoralChart: async function() {
        try {
            const res = await fetch('/api/data/analysis/rollover/sectors');
            if (!res.ok) return;
            const json = await res.json();

            const data = json.data || [];
            if (data.length === 0) return;

            // Organize by date
            const dates = [...new Set(data.map(d => d.date))].sort();
            const sectors = [...new Set(data.map(d => d.sector))].sort();

            const traces = dates.map(dt => {
                const yVals = sectors.map(sec => {
                    const match = data.find(d => d.date === dt && d.sector === sec);
                    return match ? match.avg_rollover_pct : 0;
                });
                return {
                    x: sectors,
                    y: yVals,
                    name: `Expiry ${dt}`,
                    type: 'bar',
                    text: yVals.map(v => v.toFixed(1) + '%'),
                    textposition: 'auto'
                };
            });

            const layout = {
                barmode: 'group',
                bargap: 0.1,
                bargroupgap: 0.0,
                paper_bgcolor: '#1e1e1e',
                plot_bgcolor: '#1e1e1e',
                font: { color: '#ccc' },
                margin: { t: 10, b: 60, l: 40, r: 10 },
                xaxis: { tickangle: -45 },
                yaxis: { title: 'Avg Rollover %' },
                legend: { orientation: 'h', y: 1.1 }
            };

            Plotly.newPlot('rollover-sector-chart', traces, layout, {responsive: true});

        } catch(e) {
            console.error("Failed to load sectoral chart", e);
        }
    },

    updateDynamicChart: async function() {
        const sector = document.getElementById('rollover-chart-sector-filter').value;
        const stockSelect = document.getElementById('rollover-chart-stock-filter');
        const container = document.getElementById('rollover-dynamic-chart');

        if (!sector) return;

        // If ALL or Sector selected but NO stock
        if (sector === 'ALL' || (!stockSelect.value && sector !== 'ALL')) {
            // Hide stock dropdown if ALL
            stockSelect.style.display = sector === 'ALL' ? 'none' : 'inline-block';

            // Populate stock dropdown if sector selected
            if (sector !== 'ALL') {
                const sectorStocks = this.allData.filter(d => d.sector === sector).map(d => d.symbol).sort();
                let opts = '<option value="">Select Stock</option>';
                sectorStocks.forEach(s => opts += `<option value="${s}">${s}</option>`);
                stockSelect.innerHTML = opts;
            }

            // Render Bar Chart for Current Selection (Sectors or Stocks in Sector)
            let xData = [];
            let yData = [];
            let title = '';

            if (sector === 'ALL') {
                // Avg Rollover per sector current
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
                // Rollover per stock in sector current
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
                title: { text: title, font: {size: 12} },
                paper_bgcolor: '#1e1e1e',
                plot_bgcolor: '#1e1e1e',
                font: { color: '#ccc' },
                margin: { t: 30, b: 60, l: 40, r: 10 },
                xaxis: { tickangle: -45 },
                yaxis: { title: 'Rollover %' }
            };

            Plotly.newPlot(container, [trace], layout, {responsive: true});

        } else if (stockSelect.value) {
            // Fetch 12 mo history for stock
            const symbol = stockSelect.value;
            try {
                const res = await fetch(`/api/data/analysis/rollover/history/${symbol}`);
                if (!res.ok) return;
                const json = await res.json();

                const data = json.data || [];
                const trace = {
                    x: data.map(d => d.date),
                    y: data.map(d => d.rollover_pct),
                    type: 'bar',
                    marker: { color: '#4caf50' },
                    text: data.map(d => d.rollover_pct.toFixed(1) + '%'),
                    textposition: 'auto'
                };

                const layout = {
                    title: { text: `12-Month Rollover History: ${symbol}`, font: {size: 12} },
                    paper_bgcolor: '#1e1e1e',
                    plot_bgcolor: '#1e1e1e',
                    font: { color: '#ccc' },
                    margin: { t: 30, b: 60, l: 40, r: 10 },
                    xaxis: { type: 'category' },
                    yaxis: { title: 'Rollover %' }
                };

                Plotly.newPlot(container, [trace], layout, {responsive: true});
            } catch(e) {
                console.error("Failed to load stock rollover history", e);
            }
        }
    },
"""

content = content.replace("filterData: function() {", new_methods + "    filterData: function() {")


with open("backend/ui/static/js/rolloverTool.js", "w") as f:
    f.write(content)
