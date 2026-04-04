const OiTool = {
    active: false,
    containerId: 'oi-tool-container',
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
            <style>
                .oi-row { border-bottom: 1px solid #333; }
                .oi-row:hover { background-color: #2a2a2a; cursor: pointer; }
                .oi-history-row { display: none; background-color: #1a1a1a; }
                .oi-history-row td { padding: 0 !important; border: none; }
                .oi-history-table { width: 100%; border-collapse: collapse; margin-left: 30px; font-size: 0.9em; color: #aaa; }
                .oi-history-table th, .oi-history-table td { padding: 6px 8px; border-bottom: 1px solid #222; text-align: left; }
                .oi-history-table th { background: #111; color: #888; }
            </style>
            <div style="color: #ccc; height: 100%; display: flex; flex-direction: column; flex: 1; min-width: 0;">
                <div style="display: flex; gap: 15px; margin-bottom: 15px; align-items: center; flex-shrink: 0; flex-wrap: wrap;">
                    <h2 style="margin: 0; color: #fff; font-size: 18px;">OI Analysis</h2>
                    <input type="text" id="oi-symbol" class="form-control history-input" placeholder="Search Symbol" style="width: 120px; padding: 4px;" oninput="OiTool.filterData()">
                    <select id="oi-sector-filter" class="form-control history-input" style="width: 130px; padding: 4px;" onchange="OiTool.filterData()">
                        <option value="">All Sectors</option>
                    </select>

                    <!-- Advanced Filters -->
                    <select id="oi-advanced-filter" class="form-control history-input" style="width: 180px; padding: 4px;" onchange="OiTool.filterData()">
                        <option value="">No Filter</option>
                        <option value="top_5_oi_add">Top 5 OI Additions</option>
                        <option value="top_10_oi_add">Top 10 OI Additions</option>
                        <option value="top_5_oi_red">Top 5 OI Reductions</option>
                        <option value="top_10_oi_red">Top 10 OI Reductions</option>
                        <option value="highest_oi_chg_30">Highest OI Chg (30 Days)</option>
                        <option value="highest_oi_chg_60">Highest OI Chg (60 Days)</option>
                        <option value="highest_price_chg_30">Highest Price Chg (30 Days)</option>
                        <option value="highest_price_chg_60">Highest Price Chg (60 Days)</option>
                    </select>

                    <button onclick="OiTool.loadAggregatedData()" class="btn btn-primary"><i class="fas fa-sync"></i> Refresh All</button>
                    <button onclick="OiTool.analyzeSingle()" class="btn btn-secondary">Load Single Symbol History</button>
                    <span id="oi-date-display" style="color: #888; margin-left: auto;"></span>
                </div>

                <div style="flex: 1; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; padding-bottom: 20px;">
                    <!-- Top Derived Info Panels -->
                    <div id="oi-derived-panels" style="display: flex; gap: 20px; flex-wrap: wrap;">
                        <div style="flex: 1; min-width: 300px; border: 1px solid #333; border-radius: 4px; background: #1e1e1e; padding: 10px;">
                            <h4 style="margin: 0 0 10px 0; color: #ccc; font-size: 14px; border-bottom: 1px solid #333; padding-bottom: 5px;">Top OI Additions</h4>
                            <div id="oi-top-add-chart" style="height: 180px;"></div>
                        </div>
                        <div style="flex: 1; min-width: 300px; border: 1px solid #333; border-radius: 4px; background: #1e1e1e; padding: 10px;">
                            <h4 style="margin: 0 0 10px 0; color: #ccc; font-size: 14px; border-bottom: 1px solid #333; padding-bottom: 5px;">Top OI Reductions</h4>
                            <div id="oi-top-red-chart" style="height: 180px;"></div>
                        </div>
                    </div>

                    <!-- Chart Area -->
                    <div style="height: 400px; border: 1px solid #333; border-radius: 4px; background: #1e1e1e; position: relative; flex-shrink: 0; display: flex; flex-direction: column;">
                        <div style="display: flex; justify-content: space-between; padding: 5px 10px; background: #222; border-bottom: 1px solid #333;">
                            <span style="color: #888; font-size: 12px; align-self: center;">OI Analysis</span>
                            <button class="btn btn-secondary" onclick="OiTool.exportScatterCSV()"><i class="fas fa-download"></i> CSV</button>
                        </div>
                        <div id="oi-chart-area" style="flex: 1;">
                            <p style="padding: 20px; text-align: center; color: #888;">Loading Quadrant Scatter Plot...</p>
                        </div>
                    </div>

                    <!-- Table Area -->
                    <div class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow-x: auto; flex: 1; min-height: 400px; display: flex; flex-direction: column;">
                        <div style="display: flex; justify-content: flex-end; padding: 5px 10px; background: #222; border-bottom: 1px solid #333;">
                            <button class="btn btn-secondary" onclick="exportTableToCSV('oi-analysis-table', 'OI_Analysis_Data')"><i class="fas fa-download"></i> CSV</button>
                        </div>
                        <div style="flex: 1; overflow: auto;">
                            <table class="data-table" id="oi-analysis-table" style="width: 100%;">
                                <thead style="position: sticky; top: 0; background: #222; z-index: 10;">
                                    <tr>
                                        <th style="padding: 8px; width: 30px;"></th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('symbol')">Symbol ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('sector')">Sector ↕</th>
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

            // Populate sector filter dropdown
            const sectors = new Set();
            this.allData.forEach(d => {
                if (d.sector && d.sector !== "Unknown") {
                    sectors.add(d.sector);
                }
            });
            const sectorSelect = document.getElementById('oi-sector-filter');
            if (sectorSelect) {
                const currentVal = sectorSelect.value;
                sectorSelect.innerHTML = '<option value="">All Sectors</option>';
                Array.from(sectors).sort().forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s;
                    opt.textContent = s;
                    sectorSelect.appendChild(opt);
                });
                sectorSelect.value = currentVal; // Restore selection if any
            }

            this.renderAggregatedView();

        } catch(e) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:red;">Error: ${e.message}</td></tr>`;
            chartArea.innerHTML = `<p style="color: red; padding: 20px;">Error: ${e.message}</p>`;
        }
    },

    toggleHistory: function(symbol) {
        const row = document.getElementById(`oi-history-${symbol}`);
        const icon = document.getElementById(`oi-icon-${symbol}`);
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

    renderAggregatedView: function() {
        const symbolFilter = document.getElementById('oi-symbol').value.toUpperCase().trim();
        const sectorFilter = document.getElementById('oi-sector-filter').value;
        const advFilter = document.getElementById('oi-advanced-filter').value;

        let displayData = this.allData;

        // Apply symbol / sector filter first to scope the universe
        if (symbolFilter) {
            displayData = displayData.filter(d => d.symbol.includes(symbolFilter));
        }
        if (sectorFilter) {
            displayData = displayData.filter(d => d.sector === sectorFilter);
        }

        // Save the filtered universe for generating Top Panels
        const baseUniverse = [...displayData];

        // Apply Advanced Filters (which modifies the table/scatter scope)
        if (advFilter) {
            let sortedByOI = [...displayData].sort((a,b) => b.oi_chg_pct - a.oi_chg_pct);

            if (advFilter === 'top_5_oi_add') displayData = sortedByOI.slice(0, 5);
            else if (advFilter === 'top_10_oi_add') displayData = sortedByOI.slice(0, 10);
            else if (advFilter === 'top_5_oi_red') displayData = sortedByOI.slice().reverse().slice(0, 5);
            else if (advFilter === 'top_10_oi_red') displayData = sortedByOI.slice().reverse().slice(0, 10);
            else if (advFilter.startsWith('highest_oi_chg_') || advFilter.startsWith('highest_price_chg_')) {
                // e.g., 'highest_oi_chg_30' maps to `d.oi_chg_30d` computed directly on backend
                const parts = advFilter.split('_');
                const days = parts[parts.length - 1]; // '30' or '60'
                const isPrice = advFilter.includes('price');
                const metricKey = isPrice ? `price_chg_${days}d` : `oi_chg_${days}d`;

                // Sort by absolute highest magnitude of change and take top 15
                displayData = [...displayData].sort((a,b) => {
                    const valA = Math.abs(a[metricKey] || 0);
                    const valB = Math.abs(b[metricKey] || 0);
                    return valB - valA;
                }).slice(0, 15);
            }
        }

        // Apply Standard Table Sorting
        displayData.sort((a, b) => {
            let valA = a[this.currentSortCol];
            let valB = b[this.currentSortCol];

            if (typeof valA === 'string') valA = valA.toUpperCase();
            if (typeof valB === 'string') valB = valB.toUpperCase();

            if (valA < valB) return this.currentSortAsc ? -1 : 1;
            if (valA > valB) return this.currentSortAsc ? 1 : -1;
            return 0;
        });

        this.renderDerivedPanels(baseUniverse);


        // 1. Render Table
        const tbody = document.getElementById('oi-analysis-body');
        tbody.innerHTML = '';

        if (displayData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; color:#888;">No F&O stocks found matching criteria.</td></tr>';
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

                let histHtml = '';
                if (d.history && d.history.length > 0) {
                    histHtml = `
                        <div style="padding: 10px 40px; background: #1a1a1a; border-bottom: 1px solid #333;">
                            <table style="width: 100%; border-collapse: collapse; font-size: 0.9em; text-align: left; color: #aaa;">
                            <tbody>
                    `;
                    d.history.forEach((h, idx) => {
                        let hpColor = h.price_chg_pct >= 0 ? '#4caf50' : '#f44336';
                        let hoColor = h.oi_chg_pct >= 0 ? '#4caf50' : '#f44336';
                        let rowBg = idx % 2 === 0 ? '#1f1f1f' : '#1a1a1a';
                        histHtml += `<tr style="background: ${rowBg}; border-bottom: 1px solid #2a2a2a;">
                            <td style="padding: 6px 10px; width: 20%;"><span style="color:#666;">Date:</span> ${h.date}</td>
                            <td style="padding: 6px 10px; width: 20%;"><span style="color:#666;">Price:</span> ${(h.price || 0).toFixed(2)}</td>
                            <td style="padding: 6px 10px; width: 20%; color: ${hpColor}"><span style="color:#666;">P Chg:</span> ${(h.price_chg_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 10px; width: 20%;"><span style="color:#666;">OI:</span> ${(h.oi || 0).toLocaleString()}</td>
                            <td style="padding: 6px 10px; width: 20%; color: ${hoColor}"><span style="color:#666;">OI Chg:</span> ${(h.oi_chg_pct || 0).toFixed(2)}%</td>
                        </tr>`;
                    });
                    histHtml += `</tbody></table></div>`;
                } else {
                    histHtml = `<div style="padding: 10px 40px; color: #888; background: #1a1a1a;">No historical data available</div>`;
                }

                html += `
                <tr class="deriv-row" onclick="OiTool.toggleHistory('${d.symbol}')" style="cursor: pointer; border-bottom: 1px solid #333;">
                    <td style="padding: 10px 8px; text-align: center;"><span id="oi-icon-${d.symbol}" style="font-size: 14px; color: #E88B1E; font-weight: bold;">+</span></td>
                    <td style="padding: 10px 8px;"><b>${d.symbol}</b></td>
                    <td style="padding: 10px 8px; color: #aaa;">${d.sector || ''}</td>
                    <td style="padding: 10px 8px;">${(d.price||0).toFixed(2)}</td>
                    <td style="padding: 10px 8px; color: ${pColor};">${(d.price_chg_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px;">${(d.oi||0).toLocaleString()}</td>
                    <td style="padding: 10px 8px; color: ${oColor};">${(d.oi_chg_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; color: #ccc;">${(d.total_oi||0).toLocaleString()}</td>
                    <td style="padding: 10px 8px; color: #ccc;">${(d.pcr||0).toFixed(2)}</td>
                    <td style="padding: 10px 8px; color: #ccc;">${(d.atm_iv||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; font-weight: bold; color: ${color};">${d.interpretation}</td>
                </tr>
                <tr id="oi-history-${d.symbol}" class="deriv-history-row" style="display: none;">
                    <td colspan="11" style="padding: 0;">${histHtml}</td>
                </tr>`;
            });
            tbody.innerHTML = html;

