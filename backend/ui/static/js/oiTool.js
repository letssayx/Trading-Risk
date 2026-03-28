const OiTool = {
    active: false,
    containerId: 'deriv-tab-oi',
    allData: [],

    init: function() {
        const container = document.getElementById(this.containerId);
        if (container && !container.innerHTML.includes('oi-symbol')) {
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
                    <h2 style="margin: 0; color: #fff; font-size: 18px;">OI Analysis</h2>
                    <input type="text" id="oi-symbol" class="form-control history-input" placeholder="Search/Filter Symbol" style="width: 150px; padding: 4px;" oninput="OiTool.filterData()">
                    <button onclick="OiTool.loadAggregatedData()" class="btn btn-primary"><i class="fas fa-sync"></i> Refresh All</button>
                    <button onclick="OiTool.analyzeSingle()" class="btn btn-secondary">Load Single Symbol History</button>
                    <span id="oi-date-display" style="color: #888; margin-left: auto;"></span>
                </div>

                <div style="flex: 1; display: flex; flex-direction: column; gap: 20px; overflow-y: auto;">
                    <!-- Chart Area -->
                    <div id="oi-chart-area" style="height: 400px; border: 1px solid #333; border-radius: 4px; background: #1e1e1e; position: relative; flex-shrink: 0;">
                        <p style="padding: 20px; text-align: center; color: #888;">Loading Quadrant Scatter Plot...</p>
                    </div>

                    <!-- Table Area -->
                    <div class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow-x: auto; flex: 1; min-height: 300px;">
                        <table class="data-table" id="oi-analysis-table" style="width: 100%;">
                            <thead style="position: sticky; top: 0; background: #222; z-index: 10;">
                                <tr>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('symbol')">Symbol ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('price_chg_pct')">Price Chg % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('oi_chg_pct')">OI Chg % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('interpretation')">Quadrant ↕</th>
                                </tr>
                            </thead>
                            <tbody id="oi-analysis-body">
                                <tr><td colspan="4" style="text-align:center; color:#888;">Loading...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        // Add enter key support
        const input = document.getElementById('oi-symbol');
        if (input) {
            if (typeof setupAutocomplete === 'function') {
                setupAutocomplete('oi-symbol');
            }
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    if (input.value.trim() === '') {
                        OiTool.loadAggregatedData();
                    } else {
                        OiTool.analyzeSingle();
                    }
                }
            });
            input.addEventListener('input', (e) => {
                if (input.value.trim() === '') {
                    OiTool.loadAggregatedData();
                } else {
                    if (document.getElementById('oi-analysis-body')) {
                        OiTool.filterData();
                    }
                }
            });
        }
    },

    loadAggregatedData: async function() {
        const tbody = document.getElementById('oi-analysis-body');
        const chartArea = document.getElementById('oi-chart-area');
        const dateDisplay = document.getElementById('oi-date-display');

        if (!tbody || !chartArea) return;

        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#888;">Fetching aggregated F&O data...</td></tr>';

        try {
            const res = await fetch('/api/data/analysis/oi');
            if (!res.ok) throw new Error("Failed to load aggregated OI analysis.");
            const json = await res.json();

            if (json.date) dateDisplay.textContent = `Date: ${json.date}`;

            this.allData = json.data || [];
            this.currentSortCol = 'oi_chg_pct';
            this.currentSortAsc = false;

            this.renderAggregatedView();

        } catch(e) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:red;">Error: ${e.message}</td></tr>`;
            chartArea.innerHTML = `<p style="color: red; padding: 20px;">Error: ${e.message}</p>`;
        }
    },

    renderAggregatedView: function() {
        const symbolFilter = document.getElementById('oi-symbol').value.toUpperCase().trim();
        let displayData = this.allData;

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

        // 1. Render Table
        const tbody = document.getElementById('oi-analysis-body');
        tbody.innerHTML = '';

        if (displayData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#888;">No F&O stocks found.</td></tr>';
        } else {
            let html = '';
            displayData.forEach(d => {
                let color = '#888';
                if (d.interpretation === 'Long Build Up') color = '#4caf50'; // Green
                if (d.interpretation === 'Short Covering') color = '#00bcd4'; // Blue/Cyan
                if (d.interpretation === 'Short Build Up') color = '#f44336'; // Red
                if (d.interpretation === 'Long Unwinding') color = '#ff9800'; // Orange

                let pColor = d.price_chg_pct >= 0 ? '#4caf50' : '#f44336';
                let oColor = d.oi_chg_pct >= 0 ? '#4caf50' : '#f44336';

                html += `<tr style="border-bottom: 1px solid #333;">
                    <td style="padding: 8px;"><b>${d.symbol}</b></td>
                    <td style="padding: 8px; color: ${pColor};">${d.price_chg_pct}%</td>
                    <td style="padding: 8px; color: ${oColor};">${d.oi_chg_pct}%</td>
                    <td style="padding: 8px; font-weight: bold; color: ${color};">${d.interpretation}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
        }

        // 2. Render Scatter Plot
        this.renderAggregatedChart(displayData);
    },

    renderAggregatedChart: function(data) {
        const container = document.getElementById('oi-chart-area');
        if (!container) return;

        if (data.length === 0) {
            container.innerHTML = '<p style="padding: 20px; text-align: center; color: #888;">No data for scatter plot.</p>';
            return;
        }

        const x = data.map(d => d.oi_chg_pct);
        const y = data.map(d => d.price_chg_pct);
        const text = data.map(d => d.symbol);
        const color = data.map(d => {
            if (d.interpretation === 'Long Build Up') return '#4caf50'; // Green
            if (d.interpretation === 'Short Covering') return '#00bcd4'; // Blue/Cyan
            if (d.interpretation === 'Short Build Up') return '#f44336'; // Red
            if (d.interpretation === 'Long Unwinding') return '#ff9800'; // Orange
            return '#888';
        });

        const trace = {
            x: x,
            y: y,
            mode: 'markers+text',
            type: 'scatter',
            text: text,
            textposition: 'top center',
            hovertext: data.map(d => `${d.symbol}<br>Price: ${d.price_chg_pct}%<br>OI: ${d.oi_chg_pct}%`),
            marker: { size: 10, color: color, opacity: 0.8 }
        };

        const layout = {
            title: `OI vs Price Change Quadrant Analysis`,
            paper_bgcolor: '#1e1e1e',
            plot_bgcolor: '#1e1e1e',
            font: { color: '#ccc' },
            margin: { t: 40, b: 40, l: 40, r: 40 },
            xaxis: {
                title: 'OI Change %',
                zeroline: true,
                zerolinecolor: '#888',
                gridcolor: '#333'
            },
            yaxis: {
                title: 'Price Change %',
                zeroline: true,
                zerolinecolor: '#888',
                gridcolor: '#333'
            },
            annotations: [
                { x: 0.05, y: 0.95, xref: 'paper', yref: 'paper', text: 'Short Covering', showarrow: false, font: {color: '#00bcd4', size: 16} },
                { x: 0.95, y: 0.95, xref: 'paper', yref: 'paper', text: 'Long Build Up', showarrow: false, font: {color: '#4caf50', size: 16} },
                { x: 0.05, y: 0.05, xref: 'paper', yref: 'paper', text: 'Long Unwinding', showarrow: false, font: {color: '#ff9800', size: 16} },
                { x: 0.95, y: 0.05, xref: 'paper', yref: 'paper', text: 'Short Build Up', showarrow: false, font: {color: '#f44336', size: 16} }
            ]
        };

        Plotly.newPlot(container, [trace], layout, {responsive: true});
    },

    filterData: function() {
        this.renderAggregatedView();
    },

    sortData: function(col) {
        if (this.currentSortCol === col) {
            this.currentSortAsc = !this.currentSortAsc;
        } else {
            this.currentSortCol = col;
            this.currentSortAsc = false;
        }
        this.renderAggregatedView();
    },

    analyzeSingle: async function() {
        const symbol = document.getElementById('oi-symbol').value.toUpperCase().trim();
        const chartArea = document.getElementById('oi-chart-area');

        if (!symbol) return;

        chartArea.innerHTML = '<p style="padding: 20px; text-align: center; color: #888;">Loading Single Symbol Analysis...</p>';

        // Filter the table to just show this symbol instead of hiding it
        if (this.allData && this.allData.length > 0) {
            this.filterData();
        }

        try {
            const res = await fetch(`/api/data/analysis/oi/${symbol}`);
            if (!res.ok) throw new Error("Analysis failed");
            const data = await res.json();

            // Render Single History Plotly Chart
            this.renderSingleChart(chartArea, data);

        } catch (e) {
            chartArea.innerHTML = `<p style="color: red; padding: 20px;">Error: ${e.message}</p>`;
        }
    },

    renderSingleChart: function(container, data) {
        container.innerHTML = '';

        const history = data.history || [];
        const x = history.map(d => d.oi_chg_pct);
        const y = history.map(d => d.price_chg_pct);
        const text = history.map(d => `${d.time}<br>${d.interpretation}`);
        const color = history.map(d => {
            if (d.interpretation === 'Long Build Up') return '#4caf50'; // Green
            if (d.interpretation === 'Short Covering') return '#00bcd4'; // Blue/Cyan
            if (d.interpretation === 'Short Build Up') return '#f44336'; // Red
            if (d.interpretation === 'Long Unwinding') return '#ff9800'; // Orange
            return '#888';
        });

        // Create a line tracing the path chronologically
        const tracePath = {
            x: x,
            y: y,
            mode: 'lines',
            type: 'scatter',
            line: {color: '#555', width: 1, dash: 'dot'},
            hoverinfo: 'none'
        };

        const traceMarkers = {
            x: x,
            y: y,
            mode: 'markers+text',
            type: 'scatter',
            text: history.map((d, i) => (i + 1).toString()),
            textposition: 'middle center',
            textfont: {
                color: '#fff',
                size: 10
            },
            hovertext: text,
            marker: { size: 18, color: color }
        };

        const layout = {
            title: `Single Symbol History (30d): ${data.symbol}`,
            paper_bgcolor: '#1e1e1e',
            plot_bgcolor: '#1e1e1e',
            font: { color: '#ccc' },
            margin: { t: 40, b: 40, l: 40, r: 40 },
            xaxis: {
                title: 'OI Change %',
                zeroline: true,
                zerolinecolor: '#888',
                gridcolor: '#333'
            },
            yaxis: {
                title: 'Price Change %',
                zeroline: true,
                zerolinecolor: '#888',
                gridcolor: '#333'
            },
            annotations: [
                { x: 0.05, y: 0.95, xref: 'paper', yref: 'paper', text: 'Short Covering', showarrow: false, font: {color: '#00bcd4', size: 16} },
                { x: 0.95, y: 0.95, xref: 'paper', yref: 'paper', text: 'Long Build Up', showarrow: false, font: {color: '#4caf50', size: 16} },
                { x: 0.05, y: 0.05, xref: 'paper', yref: 'paper', text: 'Long Unwinding', showarrow: false, font: {color: '#ff9800', size: 16} },
                { x: 0.95, y: 0.05, xref: 'paper', yref: 'paper', text: 'Short Build Up', showarrow: false, font: {color: '#f44336', size: 16} }
            ]
        };

        Plotly.newPlot(container, [tracePath, traceMarkers], layout, {responsive: true});
    },

    handleTick: function(tick) {
        // Update if active
    }
};

// Register with WorkbookManager
window.addEventListener('load', () => {
   if (window.WorkbookManager) {
       window.WorkbookManager.modules['oi'] = OiTool;
   }
});
