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
            <div style="color: #ccc; display: flex; flex-direction: column; flex-shrink: 0; min-width: 0;">
                <div style="display: flex; gap: 15px; margin-bottom: 15px; align-items: center; flex-shrink: 0; flex-wrap: wrap;">
                    <h2 style="margin: 0; color: #fff; font-size: 18px;">OI Analysis</h2>
                    <div style="position: relative; display: inline-flex; align-items: center;">
                        <input type="text" id="oi-symbol" class="form-control history-input" placeholder="Search Symbol" style="width: 120px; padding: 4px; padding-right: 24px;" oninput="OiTool.filterData()">
                        <button id="oi-symbol-clear" style="position: absolute; right: 4px; background: none; border: none; color: #888; cursor: pointer; display: none; font-size: 14px; padding: 0;" onclick="document.getElementById('oi-symbol').value = ''; OiTool.filterData();">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
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

                    <select id="oi-days-filter" class="form-control history-input" style="width: 100px; padding: 4px;" onchange="OiTool.loadAggregatedData(true)">
                        <option value="7">7 Days</option>
                        <option value="14">14 Days</option>
                        <option value="21">21 Days</option>
                        <option value="30" selected>30 Days</option>
                    </select>

                    <input type="date" id="oi-quadrant-date" class="form-control history-input" style="width: 130px; padding: 4px;" onchange="OiTool.loadAggregatedData(true)">

                    <label style="color:#ccc; font-size:12px;"><input type="checkbox" id="oi-force-refresh"> Force</label>
                    <button id="oi-refresh-btn" onclick="OiTool.syncAndLoadAggregatedData()" class="btn btn-primary"><i class="fas fa-sync"></i> Refresh All</button>
                    <button onclick="OiTool.analyzeSingle()" class="btn btn-secondary">Load Single Symbol History</button>
                    <span id="oi-date-display" style="color: #888; margin-left: auto;"></span>
                </div>

                <div style="flex: 1; display: flex; flex-direction: column; gap: 20px; padding-bottom: 20px;">
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
                            <span style="color: #888; font-size: 12px; align-self: center;">Derived Table View</span>
                            <button class="btn btn-secondary" onclick="OiTool.exportScatterCSV()"><i class="fas fa-download"></i> CSV</button>
                        </div>
                        <div id="oi-chart-area" style="flex: 1;">
                            <p style="padding: 20px; text-align: center; color: #888;">Loading Quadrant Scatter Plot...</p>
                        </div>
                    </div>

                    <!-- Table Area -->
                    <div class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow: hidden; flex-shrink: 0; display: flex; flex-direction: column;">
                        <div style="display: flex; justify-content: flex-end; padding: 5px 10px; background: #222; border-bottom: 1px solid #333; flex-shrink: 0;">
                            <button class="btn btn-secondary" onclick="exportTableToCSV('oi-analysis-table', 'OI_Analysis_Data')"><i class="fas fa-download"></i> CSV</button>
                        </div>
                        <div style="max-height: 400px; overflow-y: auto; overflow-x: auto;">
                            <table class="data-table" id="oi-analysis-table" style="width: 100%; table-layout: fixed;">
                                <thead style="position: sticky; top: 0; background: #222; z-index: 10;">
                                    <tr>
                                        <th style="padding: 8px; width: 30px; white-space: nowrap;"></th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('symbol')">Symbol ↕</th>
                                        <th style="padding: 8px; white-space: nowrap;">Date</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('sector')">Sector ↕</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('price')">FUT Price ↕</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('price_chg_pct')">Price Chg % ↕</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('fut_oi')">FUT OI ↕</th>
                                        <th style="padding: 8px; white-space: nowrap;">FUT OI Chg (Raw)</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('fut_oi_chg_pct')">FUT OI Chg % ↕</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('call_oi')">Call OI ↕</th>
                                        <th style="padding: 8px; white-space: nowrap;">Call OI Chg (Raw)</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('call_oi_chg_pct')">Call OI Chg % ↕</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('put_oi')">Put OI ↕</th>
                                        <th style="padding: 8px; white-space: nowrap;">Put OI Chg (Raw)</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('put_oi_chg_pct')">Put OI Chg % ↕</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('pcr')">PCR ↕</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('atm_iv')">ATM IV ↕</th>
                                        <th style="padding: 8px; cursor: pointer; white-space: nowrap;" onclick="OiTool.sortData('interpretation')">Quadrant ↕</th>
                                    </tr>
                                </thead>
                                <tbody id="oi-analysis-body">
                                    <tr><td colspan="11" style="text-align:center; color:#888;">Loading...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add enter key support
        const input = document.getElementById('oi-symbol');
        const clearBtn = document.getElementById('oi-symbol-clear');
        if (input) {
            if (typeof setupAutocomplete === 'function') {
                setupAutocomplete('oi-symbol');
            }

            input.addEventListener('input', () => {
                if (input.value.trim() !== '') {
                    clearBtn.style.display = 'block';
                } else {
                    clearBtn.style.display = 'none';
                }
            });

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

    syncAndLoadAggregatedData: async function() {
        const refreshBtn = document.getElementById('oi-refresh-btn');
        let originalBtnHtml = "";
        if (refreshBtn) {
            originalBtnHtml = refreshBtn.innerHTML;
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing Data...';
        }
        const tbody = document.getElementById('oi-analysis-body');
        if (tbody) tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; color:#888;">Checking for new F&O data and syncing...</td></tr>';

        try {
            const force = document.getElementById('oi-force-refresh') && document.getElementById('oi-force-refresh').checked;
            const syncRes = await fetch(`/api/data/analysis/oi/sync?force=${force}`, { method: 'POST' });
            if (!syncRes.ok) throw new Error("Sync failed.");
            await this.loadAggregatedData();
        } catch(e) {
            if (tbody) tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; color:red;">Sync Error: ${e.message}</td></tr>`;
        } finally {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = originalBtnHtml || '<i class="fas fa-sync"></i> Refresh All';
            }
        }
    },

    loadAggregatedData: async function() {
        const refreshBtn = document.getElementById('oi-refresh-btn');
        let originalBtnHtml = "";
        if (refreshBtn) {
            originalBtnHtml = refreshBtn.innerHTML;
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        }
        const tbody = document.getElementById('oi-analysis-body');
        const chartArea = document.getElementById('oi-chart-area');
        const dateDisplay = document.getElementById('oi-date-display');
        const daysFilter = document.getElementById('oi-days-filter');
        const days = daysFilter ? daysFilter.value : 30;
        const dateInput = document.getElementById('oi-quadrant-date');
        const targetDate = dateInput ? dateInput.value : '';

        if (!tbody || !chartArea) return;

        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; color:#888;">Fetching aggregated F&O data...</td></tr>';

        try {
            const res = await fetch(`/api/data/analysis/oi?days=${days}${targetDate ? '&target_date=' + targetDate : ''}`);
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
        } finally {
            const refreshBtn = document.getElementById('oi-refresh-btn');
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = originalBtnHtml || '<i class="fas fa-sync"></i> Refresh All';
            }
        }
    },

    toggleHistory: function(symbol) {
        const histRows = document.querySelectorAll(`.oi-history-row-${symbol}`);
        const icon = document.getElementById(`oi-icon-${symbol}`);
        if (!histRows || histRows.length === 0) return;

        let isHidden = histRows[0].style.display === 'none' || histRows[0].style.display === '';

        histRows.forEach(row => {
            row.style.display = isHidden ? 'table-row' : 'none';
        });

        if (icon) {
            icon.innerText = isHidden ? '▼' : '▶';
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

        // If a specific symbol is searched, show its 30-day history path instead of general scatter
        if (symbolFilter) {
            // Find if we have history for this single symbol
            const singleData = displayData.find(d => d.symbol === symbolFilter);
            if (singleData && singleData.history && singleData.history.length > 0) {
                // Re-use renderSingleChart instead of default scatter
                this.renderSingleChart(document.getElementById('oi-chart-area'), singleData);
            } else {
                this.renderAggregatedChart(displayData);
            }
        } else {
            this.renderAggregatedChart(displayData);
        }


        // 1. Render Table
        const tbody = document.getElementById('oi-analysis-body');
        tbody.innerHTML = '';

        if (displayData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; color:#888;">No F&O stocks found matching criteria.</td></tr>';
        } else {
            let html = '';
            displayData.forEach((d, index) => {
                let color = '#888';
                if (d.interpretation === 'Long Build Up') color = '#60a5fa'; // Blue
                if (d.interpretation === 'Short Covering') color = '#60a5fa'; // Blue
                if (d.interpretation === 'Short Build Up') color = '#ff4d4d'; // Red
                if (d.interpretation === 'Long Unwinding') color = '#ff9800'; // Orange

                let pColor = d.price_chg_pct >= 0 ? '#60a5fa' : '#ff4d4d';
                let oColor = d.oi_chg_pct >= 0 ? '#60a5fa' : '#ff4d4d';

                let futOColor = (d.fut_oi_chg_pct || 0) >= 0 ? '#60a5fa' : '#ff4d4d';
                let callOColor = (d.call_oi_chg_pct || 0) >= 0 ? '#60a5fa' : '#ff4d4d';
                let putOColor = (d.put_oi_chg_pct || 0) >= 0 ? '#60a5fa' : '#ff4d4d';

                // Use backend raw changes if available, else fallback to math
                const baseFutOi = d.fut_oi !== undefined ? d.fut_oi : d.oi || 0;
                const futOiRaw = (d.fut_oi_chg !== undefined && d.fut_oi_chg !== 0) ? d.fut_oi_chg : Math.round((baseFutOi * (d.fut_oi_chg_pct || d.oi_chg_pct || 0)) / 100) || 0;
                const callOiRaw = (d.call_oi_chg !== undefined && d.call_oi_chg !== 0) ? d.call_oi_chg : Math.round(((d.call_oi || 0) * (d.call_oi_chg_pct || 0)) / 100) || 0;
                const putOiRaw = (d.put_oi_chg !== undefined && d.put_oi_chg !== 0) ? d.put_oi_chg : Math.round(((d.put_oi || 0) * (d.put_oi_chg_pct || 0)) / 100) || 0;
                const totalOiRaw = (d.put_oi_chg !== undefined && d.call_oi_chg !== undefined && d.fut_oi_chg !== undefined && (d.put_oi_chg !== 0 || d.call_oi_chg !== 0 || d.fut_oi_chg !== 0))
                                    ? (d.put_oi_chg + d.call_oi_chg + d.fut_oi_chg)
                                    : Math.round(((d.total_oi || 0) * (d.oi_chg_pct || 0)) / 100) || 0;

                html += `<tr class="oi-row" onclick="OiTool.toggleHistory('${d.symbol}'); document.getElementById('opt-analysis-symbol').value = '${d.symbol}'; loadOptionsAnalysis();">
                    <td style="padding: 8px; text-align: center; width: 30px;"><span id="oi-icon-${d.symbol}" style="font-size: 10px;">▶</span></td>
                    <td style="padding: 8px;"><b>${d.symbol}</b></td>
                    <td style="padding: 8px; color: #aaa; white-space: nowrap;">${d.date || d.history?.[0]?.date || '-'}</td>
                    <td style="padding: 8px; color: #aaa;">${d.sector || ''}</td>
                    <td style="padding: 8px; color: #ffffff;">${(d.price || 0).toFixed(2)}</td>
                    <td style="padding: 8px; color: ${pColor};">${(d.price_chg_pct || 0).toFixed(2)}%</td>
                    <td style="padding: 8px;">${baseFutOi.toLocaleString()}</td>
                    <td style="padding: 8px; color: ${futOColor};">${futOiRaw.toLocaleString()}</td>
                    <td style="padding: 8px; color: ${futOColor};">${(d.fut_oi_chg_pct || d.oi_chg_pct || 0).toFixed(2)}%</td>
                    <td style="padding: 8px;">${(d.call_oi || 0).toLocaleString()}</td>
                    <td style="padding: 8px; color: ${callOColor};">${callOiRaw.toLocaleString()}</td>
                    <td style="padding: 8px; color: ${callOColor};">${(d.call_oi_chg_pct || 0).toFixed(2)}%</td>
                    <td style="padding: 8px;">${(d.put_oi || 0).toLocaleString()}</td>
                    <td style="padding: 8px; color: ${putOColor};">${putOiRaw.toLocaleString()}</td>
                    <td style="padding: 8px; color: ${putOColor};">${(d.put_oi_chg_pct || 0).toFixed(2)}%</td>
                    <td style="padding: 8px;">${d.pcr ? d.pcr.toFixed(2) : '-'}</td>
                    <td style="padding: 8px;">${(d.atm_iv !== undefined && d.atm_iv !== null && d.atm_iv !== 0) ? (typeof d.atm_iv === "string" ? parseFloat(d.atm_iv) : d.atm_iv).toFixed(2) + "%" : "-"}</td>
                    <td style="padding: 8px; font-weight: bold; color: ${color};">${d.interpretation}</td>
                </tr>`;

                if (d.history && d.history.length > 1) {
                    const daysFilter = document.getElementById('oi-days-filter');
                    const days = daysFilter ? parseInt(daysFilter.value, 10) : 30;
                    d.history.slice(1, days).forEach(h => {
                        let hpColor = h.price_chg_pct >= 0 ? '#60a5fa' : '#ff4d4d';
                        let hoColor = h.oi_chg_pct >= 0 ? '#60a5fa' : '#ff4d4d';
                        // Matching exact columns: [Icon, Symbol/Date, Sector, FUT Price, Price Chg %, OI, OI Chg %, Total OI, PCR, ATM IV, Quadrant]
                        let futOColor = (h.fut_oi_chg_pct || 0) >= 0 ? '#60a5fa' : '#ff4d4d';
                        let callOColor = (h.call_oi_chg_pct || 0) >= 0 ? '#60a5fa' : '#ff4d4d';
                        let putOColor = (h.put_oi_chg_pct || 0) >= 0 ? '#60a5fa' : '#ff4d4d';
                        let baseFutOiH = h.fut_oi !== undefined ? h.fut_oi : h.oi || 0;

                        html += `<tr class="oi-history-row-${d.symbol}" style="background: #151515; border-bottom: 1px solid #222; font-size: 0.85em; display: none;">
                            <td style="padding: 6px 8px; width: 30px; border-right: 1px solid #333;"></td>
                            <td style="padding: 6px 8px;"></td>
                            <td style="padding: 6px 8px; color: #888; white-space: nowrap;">└ ${h.date}</td>
                            <td style="padding: 6px 8px; color: #ccc;">${h.sector || '-'}</td>
                            <td style="padding: 6px 8px; color: #ffffff;">${(h.price || 0).toFixed(2)}</td>
                            <td style="padding: 6px 8px; color: ${hpColor}">${(h.price_chg_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 8px; color: #ccc;">${baseFutOiH.toLocaleString()}</td>
                            <td style="padding: 6px 8px; color: ${futOColor};">${(h.fut_oi_chg || 0).toLocaleString()}</td>
                            <td style="padding: 6px 8px; color: ${futOColor};">${(h.fut_oi_chg_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 8px; color: #ccc;">${(h.call_oi || 0).toLocaleString()}</td>
                            <td style="padding: 6px 8px; color: ${callOColor};">${(h.call_oi_chg || 0).toLocaleString()}</td>
                            <td style="padding: 6px 8px; color: ${callOColor};">${(h.call_oi_chg_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 8px; color: #ccc;">${(h.put_oi || 0).toLocaleString()}</td>
                            <td style="padding: 6px 8px; color: ${putOColor};">${(h.put_oi_chg || 0).toLocaleString()}</td>
                            <td style="padding: 6px 8px; color: ${putOColor};">${(h.put_oi_chg_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 8px; color: #ccc;">${(h.pcr || 0).toFixed(2)}</td>
                            <td style="padding: 6px 8px; color: #ccc;">${(h.atm_iv !== undefined && h.atm_iv !== null && h.atm_iv !== 0) ? (typeof h.atm_iv === "string" ? parseFloat(h.atm_iv) : h.atm_iv).toFixed(2) + "%" : "-"}</td>
                            <td style="padding: 6px 8px; color: #555;">-</td>
                        </tr>`;
                    });
                }
            });
            tbody.innerHTML = html;
        }

    },

    renderDerivedPanels: function(universe) {
        let sortedByOI = [...universe].sort((a,b) => b.oi_chg_pct - a.oi_chg_pct);
        const top5Add = sortedByOI.slice(0, 5);
        const top5Red = sortedByOI.slice().reverse().slice(0, 5);

        const addDom = document.getElementById('oi-top-add-chart');
        const redDom = document.getElementById('oi-top-red-chart');

        if (!addDom || !redDom) return;

        const buildTableHTML = (dataSubset) => {
            let html = `<table style="width: 100%; border-collapse: collapse; font-size: 0.85em; text-align: left;">
                <thead>
                    <tr style="border-bottom: 1px solid #333; color: #888;">
                        <th style="padding: 4px;">Symbol</th>
                        <th style="padding: 4px;">OI Chg %</th>
                        <th style="padding: 4px;">Price</th>
                        <th style="padding: 4px;">Price Chg %</th>
                        <th style="padding: 4px;">Inference</th>
                    </tr>
                </thead>
                <tbody>`;

            dataSubset.forEach(d => {
                let oColor = d.oi_chg_pct >= 0 ? '#60a5fa' : '#ff4d4d';
                let pColor = d.price_chg_pct >= 0 ? '#60a5fa' : '#ff4d4d';
                html += `<tr style="border-bottom: 1px solid #222;">
                    <td style="padding: 4px; font-weight: bold; color: #ccc;">${d.symbol}</td>
                    <td style="padding: 4px; color: ${oColor};">${(d.oi_chg_pct || 0).toFixed(2)}%</td>
                    <td style="padding: 4px; color: #ffffff;">${(d.price || 0).toFixed(2)}</td>
                    <td style="padding: 4px; color: ${pColor};">${(d.price_chg_pct || 0).toFixed(2)}%</td>
                    <td style="padding: 4px; color: ${oColor};">${d.interpretation || '-'}</td>
                </tr>`;
            });

            html += `</tbody></table>`;
            return html;
        };

        // Dispose previous charts to prevent memory leaks if they existed
        if (window.oiAddChart) { window.oiAddChart.dispose(); window.oiAddChart = null; }
        if (window.oiRedChart) { window.oiRedChart.dispose(); window.oiRedChart = null; }

        addDom.innerHTML = buildTableHTML(top5Add);
        redDom.innerHTML = buildTableHTML(top5Red);
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
            if (d.interpretation === 'Long Build Up') return '#60a5fa'; // Blue
            if (d.interpretation === 'Short Covering') return '#60a5fa'; // Blue
            if (d.interpretation === 'Short Build Up') return '#ff4d4d'; // Red
            if (d.interpretation === 'Long Unwinding') return '#ff9800'; // Orange
            return '#888';
        });

        // Ensure axes are symmetric around 0 so the quadrants are mathematically correct relative to paper corners
        let maxAbsX = Math.max(...x.map(Math.abs), 1) * 1.1; // fallback to 1 to avoid 0 range
        let maxAbsY = Math.max(...y.map(Math.abs), 1) * 1.1;

        // Clip extreme outliers for better default zoom scale (e.g. 95th percentile)
        let sortedAbsX = [...x.map(Math.abs)].sort((a, b) => a - b);
        let sortedAbsY = [...y.map(Math.abs)].sort((a, b) => a - b);
        let perc95X = sortedAbsX[Math.floor(sortedAbsX.length * 0.95)] || maxAbsX;
        let perc95Y = sortedAbsY[Math.floor(sortedAbsY.length * 0.95)] || maxAbsY;

        let zoomRangeX = Math.max(perc95X * 1.2, 5);
        let zoomRangeY = Math.max(perc95Y * 1.2, 2);

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
                zerolinewidth: 2,
                zerolinecolor: '#ccc',
                gridcolor: '#333',
                range: [-zoomRangeX, zoomRangeX]
            },
            yaxis: {
                title: 'Price Change %',
                zeroline: true,
                zerolinewidth: 2,
                zerolinecolor: '#ccc',
                gridcolor: '#333',
                range: [-zoomRangeY, zoomRangeY]
            },
            annotations: [
                { x: 0.05, y: 0.95, xref: 'paper', yref: 'paper', text: 'Short Covering', showarrow: false, font: {color: '#60a5fa', size: 16} },
                { x: 0.95, y: 0.95, xref: 'paper', yref: 'paper', text: 'Long Build Up', showarrow: false, font: {color: '#60a5fa', size: 16} },
                { x: 0.05, y: 0.05, xref: 'paper', yref: 'paper', text: 'Long Unwinding', showarrow: false, font: {color: '#ff9800', size: 16} },
                { x: 0.95, y: 0.05, xref: 'paper', yref: 'paper', text: 'Short Build Up', showarrow: false, font: {color: '#ff4d4d', size: 16} }
            ],
            dragmode: 'zoom'
        };

        const config = {
            responsive: true,
            scrollZoom: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d', 'pan2d']
        };

        Plotly.newPlot(container, [trace], layout, config);
    },

    filterData: function() {
        const input = document.getElementById('oi-symbol');
        const clearBtn = document.getElementById('oi-symbol-clear');
        if (input && clearBtn) {
            clearBtn.style.display = input.value.trim() !== '' ? 'block' : 'none';
        }
        if (!this.allData || this.allData.length === 0) {
            this.loadAggregatedData();
        } else {
            this.renderAggregatedView();
        }
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

        const singleBtn = document.querySelector('button[onclick="OiTool.analyzeSingle()"]');
        let originalSingleBtnHtml = "";
        if (singleBtn) {
            originalSingleBtnHtml = singleBtn.innerHTML;
            singleBtn.disabled = true;
            singleBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        }
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
        } finally {
            const singleBtn = document.querySelector('button[onclick="OiTool.analyzeSingle()"]');
            if (singleBtn) {
                singleBtn.disabled = false;
                singleBtn.innerHTML = originalSingleBtnHtml || 'Load Single Symbol History';
            }
        }
    },

    renderSingleChart: function(container, data) {
        container.innerHTML = '';

        const history = (data.history || []).slice().reverse(); // Reverse so latest is last in array
        const x = history.map(d => d.oi_chg_pct);
        const y = history.map(d => d.price_chg_pct);
        const text = history.map(d => `${d.time}<br>${d.interpretation}`);
        const color = history.map(d => {
            if (d.interpretation === 'Long Build Up') return '#60a5fa'; // Blue
            if (d.interpretation === 'Short Covering') return '#60a5fa'; // Blue
            if (d.interpretation === 'Short Build Up') return '#ff4d4d'; // Red
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
            text: history.map((d, i) => {
                if (i === history.length - 1) return (i + 1).toString() + "\n(Latest)";
                return (i + 1).toString();
            }),
            textposition: history.map((d, i) => i === history.length - 1 ? 'top center' : 'middle center'),
            textfont: {
                color: history.map((d, i) => i === history.length - 1 ? '#ffcc00' : '#fff'),
                size: history.map((d, i) => i === history.length - 1 ? 12 : 10),
                weight: history.map((d, i) => i === history.length - 1 ? 'bold' : 'normal')
            },
            hovertext: text,
            marker: {
                size: history.map((d, i) => i === history.length - 1 ? 24 : 18),
                color: history.map((d, i, arr) => i === history.length - 1 ? '#ffffff' : color[i]),
                line: {
                    color: history.map((d, i) => i === history.length - 1 ? '#ffcc00' : 'transparent'),
                    width: history.map((d, i) => i === history.length - 1 ? 2 : 0)
                }
            }
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
                { x: 0.05, y: 0.95, xref: 'paper', yref: 'paper', text: 'Short Covering', showarrow: false, font: {color: '#60a5fa', size: 16} },
                { x: 0.95, y: 0.95, xref: 'paper', yref: 'paper', text: 'Long Build Up', showarrow: false, font: {color: '#60a5fa', size: 16} },
                { x: 0.05, y: 0.05, xref: 'paper', yref: 'paper', text: 'Long Unwinding', showarrow: false, font: {color: '#ff9800', size: 16} },
                { x: 0.95, y: 0.05, xref: 'paper', yref: 'paper', text: 'Short Build Up', showarrow: false, font: {color: '#ff4d4d', size: 16} }
            ]
        };

        Plotly.newPlot(container, [tracePath, traceMarkers], layout, {responsive: true});
    },

    exportScatterCSV: function() {
        const symbolFilter = document.getElementById('oi-symbol').value.toUpperCase().trim();
        const sectorFilter = document.getElementById('oi-sector-filter').value;
        let displayData = this.allData;

        if (symbolFilter) {
            displayData = displayData.filter(d => d.symbol.includes(symbolFilter));
        }
        if (sectorFilter) {
            displayData = displayData.filter(d => d.sector === sectorFilter);
        }

        if (!displayData || displayData.length === 0) {
            alert("No data to export.");
            return;
        }

        let csv = "Symbol,Sector,Price Change %,OI Change %,Quadrant\n";
        displayData.forEach((d, index) => {
            csv += `"${d.symbol}","${d.sector || ''}","${d.price_chg_pct}","${d.oi_chg_pct}","${d.interpretation}"\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `OI_Scatter_Data_${new Date().toISOString().slice(0,10)}.csv`;
        link.click();
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
