const RolloverTool = {
    active: false,
    containerId: 'deriv-tab-rollover',
    allData: [],

    init: function() {
        const container = document.getElementById(this.containerId);
        if (container && !container.innerHTML.includes('rollover-symbol')) {
            this.render(container);
            this.loadAggregatedData();
        }
    },

    open: function() {
        this.active = true;
        this.init();
    },

    close: function() {
        this.active = false;
    },

    render: function(container) {
        container.innerHTML = `
            <div style="color: #ccc; height: 100%; display: flex; flex-direction: column;">
                <div style="display: flex; gap: 15px; margin-bottom: 15px; align-items: center; flex-shrink: 0;">
                    <h2 style="margin: 0; color: #fff; font-size: 18px;">Rollover Analysis</h2>
                    <input type="text" id="rollover-symbol" class="form-control history-input" placeholder="Search/Filter Symbol" style="width: 150px; padding: 4px;" oninput="RolloverTool.filterData()">
                    <button onclick="RolloverTool.loadAggregatedData()" class="btn btn-primary"><i class="fas fa-sync"></i> Refresh All</button>
                    <button onclick="RolloverTool.analyzeSingle()" class="btn btn-secondary">Load Single Details</button>
                    <button class="btn btn-secondary" onclick="exportTableToCSV('rollover-analysis-table', 'Rollover_Analysis')"><i class="fas fa-download"></i> CSV</button>
                    <span id="rollover-date-display" style="color: #888; margin-left: auto;"></span>
                </div>

                <div id="rollover-results" style="flex: 1; overflow: auto; display: flex; flex-direction: column; gap: 20px;">
                    <!-- Table Area -->
                    <div class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow-x: auto; flex: 1;">
                        <table class="data-table" id="rollover-analysis-table" style="width: 100%;">
                            <thead style="position: sticky; top: 0; background: #222; z-index: 10;">
                                <tr>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('symbol')">Symbol ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_pct')">Rollover % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost')">Spread (Pts) ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost_pct')">Cost % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('near_oi')">Near OI ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('total_oi')">Total OI ↕</th>
                                </tr>
                            </thead>
                            <tbody id="rollover-analysis-body">
                                <tr><td colspan="6" style="text-align:center; color:#888;">Loading Rollover Data...</td></tr>
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
                    // Automatically reload the full table view when cleared
                    RolloverTool.loadAggregatedData();
                } else {
                    // Just filter the table locally while typing
                    if (document.getElementById('rollover-analysis-body')) {
                        RolloverTool.filterData();
                    }
                }
            });
        }
    },

    loadAggregatedData: async function() {
        const tbody = document.getElementById('rollover-analysis-body');
        const dateDisplay = document.getElementById('rollover-date-display');

        // Remove single symbol details if present
        const detailsDiv = document.getElementById('rollover-single-details');
        if (detailsDiv) {
            detailsDiv.remove();
        }

        if (!tbody) return;

        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#888;">Fetching aggregated F&O Rollover data...</td></tr>';

        try {
            const res = await fetch('/api/data/analysis/rollover');
            if (!res.ok) throw new Error("Failed to load rollover data.");
            const json = await res.json();

            if (json.date) dateDisplay.textContent = `Date: ${json.date}`;

            this.allData = json.data || [];

            // Populate Sector Filter
            const sectors = [...new Set(this.allData.map(d => d.sector))].filter(s => s && s !== 'Unknown').sort();
            const sectorFilter = document.getElementById('rollover-sector-filter');
            const chartSectorFilter = document.getElementById('rollover-chart-sector-filter');
            if (sectorFilter && sectorFilter.options.length <= 1) {
                sectors.forEach(s => {
                    sectorFilter.innerHTML += `<option value="${s}">${s}</option>`;
                });
            }
            if (chartSectorFilter && chartSectorFilter.options.length <= 1) {
                sectors.forEach(s => {
                    chartSectorFilter.innerHTML += `<option value="${s}">${s}</option>`;
                });
            }

            this.loadSectoralChart();
            this.updateDynamicChart();

            this.currentSortCol = 'rollover_pct';
            this.currentSortAsc = false;

            this.renderAggregatedView();

        } catch(e) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:red;">Error: ${e.message}</td></tr>`;
        }
    },

    renderAggregatedView: function() {
        const symbolFilter = document.getElementById('rollover-symbol').value.toUpperCase().trim();
        const sectorFilter = document.getElementById('rollover-sector-filter').value;
        let displayData = this.allData;

        if (sectorFilter) {
            displayData = displayData.filter(d => d.sector === sectorFilter);
        }

        if (symbolFilter) {
            displayData = this.allData.filter(d => d.symbol.includes(symbolFilter));
        }

        // Sort Data
        displayData.sort((a, b) => {
            let valA = a[this.currentSortCol];
            let valB = b[this.currentSortCol];

            if (typeof valA === 'string') valA = valA.toUpperCase();
            if (typeof valB === 'string') valB = valB.toUpperCase();

            if (valA < valB) return this.currentSortAsc ? -1 : 1;
            if (valA > valB) return this.currentSortAsc ? 1 : -1;
            return 0;
        });

        // Render Table
        const tbody = document.getElementById('rollover-analysis-body');
        if (tbody) {
            let html = '';
            displayData.forEach(d => {
                let rollColor = d.rollover_pct > 80 ? '#4caf50' : (d.rollover_pct < 50 ? '#f44336' : '#ccc');
                let costColor = d.rollover_cost_pct > 0 ? '#4caf50' : '#f44336';
                let pColor = d.price_chg_pct >= 0 ? '#4caf50' : '#f44336';
                let oColor = d.oi_chg_pct >= 0 ? '#4caf50' : '#f44336';

                let histHtml = '';
                if (d.history && d.history.length > 0) {
                    histHtml = `
                        <table class="data-table" style="width: 95%; margin: 10px auto; background: #222; border: 1px solid #444;">
                        <thead>
                            <tr style="background: #333;">
                                <th style="padding: 4px;">Date</th>
                                <th style="padding: 4px;">Price</th>
                                <th style="padding: 4px;">Price Chg %</th>
                                <th style="padding: 4px;">OI</th>
                                <th style="padding: 4px;">OI Chg %</th>
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
        }
    },


    toggleHistory: function(symbol) {
        const row = document.getElementById(`roll-history-${symbol}`);
        const icon = document.getElementById(`roll-icon-${symbol}`);
        if (row.style.display === 'table-row') {
            row.style.display = 'none';
            icon.innerText = '▶';
        } else {
            row.style.display = 'table-row';
            icon.innerText = '▼';
        }
    },

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
    filterData: function() {
        if (!document.getElementById('rollover-analysis-body')) return;
        this.renderAggregatedView();
    },

    sortData: function(col) {
        if (!document.getElementById('rollover-analysis-body')) return;

        if (this.currentSortCol === col) {
            this.currentSortAsc = !this.currentSortAsc;
        } else {
            this.currentSortCol = col;
            this.currentSortAsc = false;
        }
        this.renderAggregatedView();
    },

    analyzeSingle: async function() {
        const symbol = document.getElementById('rollover-symbol').value.toUpperCase().trim();
        let detailsDiv = document.getElementById('rollover-single-details');
        const resultsDiv = document.getElementById('rollover-results');

        if (!symbol) return;

        if (!detailsDiv) {
            detailsDiv = document.createElement('div');
            detailsDiv.id = 'rollover-single-details';
            resultsDiv.insertBefore(detailsDiv, resultsDiv.firstChild);
        }

        detailsDiv.innerHTML = '<p style="text-align:center; color:#888; margin-top: 20px;">Loading Single Symbol Details...</p>';

        try {
            const res = await fetch(`/api/data/analysis/rollover/${symbol}`);
            if (!res.ok) throw new Error("Analysis failed");
            const data = await res.json();

            if (data.error) throw new Error(data.error);

            let html = `<div style="padding: 20px; border: 1px solid #444; background: #222; border-radius: 4px; margin-top: 10px;">
                <h4 style="margin-top: 0; color: #fff;">${symbol} Detailed Rollover Stats</h4>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 10px;">
                    <div>
                        <div style="font-size: 0.9em; color: #888;">Rollover %</div>
                        <div style="font-size: 1.5em; color: #00bcd4; font-weight: bold;">${data.rollover_pct}%</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; color: #888;">Rollover Cost (Spread)</div>
                        <div style="font-size: 1.5em; color: ${data.rollover_cost >= 0 ? '#4caf50' : '#f44336'};">${data.rollover_cost} (${data.rollover_cost_pct}%)</div>
                    </div>
                </div>

                <table style="width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 0.9em; text-align: left;">
                    <thead>
                        <tr style="background: #333;">
                            <th style="padding: 8px; border: 1px solid #444;">Contract</th>
                            <th style="padding: 8px; border: 1px solid #444;">Expiry</th>
                            <th style="padding: 8px; border: 1px solid #444;">Price</th>
                            <th style="padding: 8px; border: 1px solid #444;">OI</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 8px; border: 1px solid #444; color: #ccc;">Near Month</td>
                            <td style="padding: 8px; border: 1px solid #444; color: #ccc;">${data.near_month.expiry}</td>
                            <td style="padding: 8px; border: 1px solid #444; color: #ccc;">${data.near_month.price}</td>
                            <td style="padding: 8px; border: 1px solid #444; color: #ccc;">${data.near_month.oi}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border: 1px solid #444; color: #ccc;">Next Month</td>
                            <td style="padding: 8px; border: 1px solid #444; color: #ccc;">${data.next_month.expiry}</td>
                            <td style="padding: 8px; border: 1px solid #444; color: #ccc;">${data.next_month.price}</td>
                            <td style="padding: 8px; border: 1px solid #444; color: #ccc;">${data.next_month.oi}</td>
                        </tr>
                    </tbody>
                </table>
                <p style="color: #888; font-size: 0.85em; margin-top: 15px;">To return to the all F&O view, clear the search and click "Refresh All".</p>
            </div>`;

            detailsDiv.innerHTML = html;
            // Also filter the table to just this symbol
            this.filterData();

        } catch (e) {
            detailsDiv.innerHTML = `<p style="color: red; text-align:center; margin-top: 20px;">Error: ${e.message}</p>`;
        }
    },

    handleTick: function(tick) {
        // Update
    }
};

// Register
window.addEventListener('load', () => {
   if (window.WorkbookManager) {
       window.WorkbookManager.modules['rollover'] = RolloverTool;
   }
});
