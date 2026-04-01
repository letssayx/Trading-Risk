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
                    <button onclick="exportTableToCSV('rollover-analysis-table', 'Rollover_Analysis')" class="btn btn-secondary"><i class="fas fa-download"></i> CSV</button>
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
            this.currentSortCol = 'rollover_pct';
            this.currentSortAsc = false;

            this.renderAggregatedView();

        } catch(e) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:red;">Error: ${e.message}</td></tr>`;
        }
    },

    renderAggregatedView: function() {
        const symbolFilter = document.getElementById('rollover-symbol').value.toUpperCase().trim();
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

        // Render Table
        const tbody = document.getElementById('rollover-analysis-body');
        tbody.innerHTML = '';

        if (displayData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#888;">No F&O stocks found.</td></tr>';
        } else {
            let html = '';
            displayData.forEach(d => {
                let costColor = d.rollover_cost >= 0 ? '#4caf50' : '#f44336';
                let rollColor = d.rollover_pct >= 80 ? '#00bcd4' : '#ccc';

                html += `<tr style="border-bottom: 1px solid #333;">
                    <td style="padding: 8px;"><b>${d.symbol}</b></td>
                    <td style="padding: 8px; color: ${rollColor}; font-weight: bold;">${d.rollover_pct}%</td>
                    <td style="padding: 8px; color: ${costColor};">${d.rollover_cost}</td>
                    <td style="padding: 8px; color: ${costColor};">${d.rollover_cost_pct}%</td>
                    <td style="padding: 8px; color: #888;">${d.near_oi}</td>
                    <td style="padding: 8px; color: #888;">${d.total_oi}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
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
