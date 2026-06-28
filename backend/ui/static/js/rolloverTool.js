const RolloverTool = {
    active: false,
    containerId: 'deriv-tab-rollover',
    allData: [],

    init: function() {
        const container = document.getElementById(this.containerId);
        if (container && !container.innerHTML.includes('rollover-symbol')) {
            this.render(container);
            const symInput = document.getElementById("rollover-symbol");
            if (symInput && !symInput.value.trim()) {
              symInput.value = "NIFTY";
            }
            this.loadAggregatedData();
            this.analyzeSingle();
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

                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="position: relative;">
                            <input type="text" id="rollover-symbol" class="form-control history-input" placeholder="Search/Filter Symbol" style="width: 150px; padding: 4px; padding-right: 20px;" oninput="RolloverTool.filterData()">
                            <span id="rollover-clear-search" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); cursor: pointer; color: #888; display: none;" onclick="document.getElementById('rollover-symbol').value=''; RolloverTool.filterData(); RolloverTool.loadAggregatedData(); this.style.display='none';">✖</span>
                        </div>
                        <button onclick="RolloverTool.analyzeSingle()" class="btn btn-secondary">Load Single Details</button>
                    </div>

                    <div style="display: flex; gap: 10px; align-items: center; margin-left: 20px; border-left: 1px solid #444; padding-left: 15px;">
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;" title="Show Month-on-Month expiry rollover instead of daily progression">
                            <input type="checkbox" id="rollover-mom-checkbox" checked onchange="RolloverTool.loadAggregatedData(); if(document.getElementById('rollover-symbol').value) { RolloverTool.analyzeSingle(); }"> Month-on-Month
                        </label>
                    </div>

                    <div style="display: flex; gap: 10px; align-items: center; margin-left: 20px; border-left: 1px solid #444; padding-left: 15px;">
                        <span style="color: #aaa; font-size: 13px;">History Range:</span>
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;">
                            <input type="radio" name="rollover_days" value="7" onchange="RolloverTool.loadAggregatedData()"> 7 Days
                        </label>
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;">
                            <input type="radio" name="rollover_days" value="14" checked onchange="RolloverTool.loadAggregatedData()"> 14 Days
                        </label>
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;">
                            <input type="radio" name="rollover_days" value="30" onchange="RolloverTool.loadAggregatedData()"> 30 Days
                        </label>
                    </div>

                    <div style="display: flex; gap: 10px; align-items: center; margin-left: auto;">
                        <label style="color:#ccc; font-size:12px;"><input type="checkbox" id="rollover-force-refresh"> Force</label>
                        <button id="rollover-refresh-btn" onclick="RolloverTool.syncAndLoadAggregatedData()" class="btn btn-primary"><i class="fas fa-sync"></i> Refresh All</button>
                    </div>

                    <span id="rollover-date-display" style="color: #888; margin-left: auto;"></span>
                </div>

                <div id="rollover-results" style="flex: 1; overflow: auto; display: flex; flex-direction: column; gap: 20px; padding-bottom: 20px;">
                    <!-- 1. Single Scrip Details Area -->
                    <div id="rollover-single-details" style="flex-shrink: 0; min-height: 100px; display: block;"></div>

                    <!-- 2. Matrix Table Area (New) -->
                    <div style="flex-shrink: 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px; align-items: flex-end;">
                            <h4 style="margin: 0; color: #fff;">Historical 24-Month Matrix</h4>
                            <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px; margin-right: 15px;" onclick="RolloverTool.exportMatrixExcel()"><i class="fas fa-download"></i> Excel</button>
                        </div>
                        <div id="rollover-matrix-container" class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow-x: auto; min-height: 400px; max-height: calc(100vh - 450px); overflow-y: auto; display: block;">
                            <p style="text-align:center; color:#888; padding: 20px;">Fetching Historical F&O Matrix...</p>
                        </div>
                    </div>

                    <!-- 3. Charts Area -->
                    <div style="display: flex; gap: 20px; height: 350px; flex-shrink: 0; width: 100%;">
                        <div style="flex: 1; background: #1e1e1e; border: 1px solid #333; border-radius: 4px; padding: 10px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                                <div style="display:flex; gap:10px;">
                                    <select id="rollover-chart-sector-filter" class="form-control history-input" style="padding: 2px 5px;" onchange="RolloverTool.updateDynamicChart()">
                                        <option value="ALL">All Sectors Avg</option>
                                    </select>
                                    <select id="rollover-chart-stock-filter" class="form-control history-input" style="padding: 2px 5px; display:none;" onchange="RolloverTool.updateDynamicChart()">
                                        <option value="">Select Stock</option>
                                    </select>
                                </div>
                                <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="if(window.rolloverDynamicChartInstance) exportChartDataToExcel(window.rolloverDynamicChartInstance, 'Dynamic_Rollover')"><i class="fas fa-download"></i> Excel</button>
                            </div>
                            <div id="rollover-dynamic-chart" style="width: 100%; height: calc(100% - 30px);"></div>
                        </div>
                    </div>

                    <!-- 4. Table Area (Original) -->
                    <div style="flex-shrink: 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px; align-items: flex-end;">
                            <h4 style="margin: 0; color: #fff;">Daily F&O Rollover Data</h4>
                            <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="exportTableToExcel('rollover-analysis-table', 'Rollover_Analysis')"><i class="fas fa-download"></i> Excel</button>
                        </div>
                        <div class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow-x: auto; min-height: 400px; max-height: calc(100vh - 450px); overflow-y: auto;">
                            <table class="data-table" id="rollover-analysis-table" style="width: 100%; table-layout: fixed;">
                                <thead style="position: sticky; top: 0; background: #222; z-index: 10;">
                                    <tr>
                                        <th style="padding: 8px; width: 30px;"></th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('symbol')">Symbol ↕</th>
                                        <th style="padding: 8px;">Date</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_pct')">Rollover % ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost')">Spread (Pts) ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('bps')">BPS ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost_pct')">Cost % ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('fut_close')">FUT Price ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('price_chg_pct')">Price Chg % ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('total_oi')">Total OI ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('oi_chg_pct')">OI Chg % ↕</th>
                                    </tr>
                                </thead>
                                <tbody id="rollover-analysis-body">
                                    <tr><td colspan="11" style="text-align:center; color:#888;">Loading Rollover Data...</td></tr>
                                </tbody>
                            </table>
                        </div>
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
                const clearBtn = document.getElementById('rollover-clear-search');
                if (clearBtn) clearBtn.style.display = input.value.trim() !== '' ? 'block' : 'none';

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

    syncAndLoadAggregatedData: async function(forceMasterSync = false) {
        const btn = document.getElementById('rollover-refresh-btn');
        const forceCb = document.getElementById('rollover-force-refresh');
        const isForceCb = forceCb && forceCb.checked;
        const isForce = forceMasterSync || isForceCb;
        const originalText = btn ? btn.innerHTML : '';

        if (btn) {
            btn.innerHTML = "<i class='fas fa-spinner fa-spin'></i> Syncing...";
            btn.disabled = true;
        }

        try {
            const syncRes = await fetch(`/api/data/analysis/rollover/sync?force=${isForce}`, { method: 'POST' });
            if (!syncRes.ok) console.warn("Sync failed or not supported.");
        } catch (e) {
            console.error("Sync error:", e);
        }

        await this.loadAggregatedData();

        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
        if (forceCb) forceCb.checked = false;
    },

    loadAggregatedData: async function() {
        const tbody = document.getElementById('rollover-analysis-body');
        const dateDisplay = document.getElementById('rollover-date-display');



        if (!tbody) return;

        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#888;">Fetching aggregated F&O Rollover data...</td></tr>';

        try {
            let days = '14';
            const daysRadio = document.querySelector('input[name="rollover_days"]:checked');
            if (daysRadio) {
                days = daysRadio.value;
            }
            const momCheckbox = document.getElementById('rollover-mom-checkbox');
            const isMoM = momCheckbox ? momCheckbox.checked : false;

            const res = await fetch(`/api/data/analysis/rollover?days=${days}&expiry_only=${isMoM}`);
            if (!res.ok) throw new Error("Failed to load rollover data.");
            const json = await res.json();

            if (json.date) dateDisplay.textContent = `Date: ${json.date}`;

            this.allData = json.data || [];
            this.currentSortCol = 'rollover_pct';
            this.currentSortAsc = false;

            // Populate sector filter for the dynamic chart
            const sectors = new Set();
            this.allData.forEach(d => {
                if (d.sector && d.sector !== "Unknown") sectors.add(d.sector);
            });
            const sectorSelect = document.getElementById('rollover-chart-sector-filter');
            if (sectorSelect) {
                const currentVal = sectorSelect.value;
                sectorSelect.innerHTML = '<option value="ALL">All Sectors Avg</option>';
                Array.from(sectors).sort().forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s;
                    opt.textContent = s;
                    sectorSelect.appendChild(opt);
                });
                sectorSelect.value = currentVal;
            }

            this.renderAggregatedView();

            // Also load the charts since data is refreshed
            this.updateDynamicChart();
            this.renderMatrix(this.allData, isMoM);

        } catch(e) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:red;">Error: ${e.message}</td></tr>`;
        }
    },

    renderAggregatedView: function() {
        const symbolFilter = document.getElementById('rollover-symbol').value.toUpperCase().trim();
        let displayData = this.allData;

        if (symbolFilter) {
            displayData = this.allData.filter(d => d.symbol.includes(symbolFilter));
        }

        // Sort Data
        if (this.currentSortCol === 'bps') {
            displayData.sort((a, b) => {
                let valA = (a.price && a.price > 0) ? ((a.rollover_cost / a.price) * 10000) : 0;
                let valB = (b.price && b.price > 0) ? ((b.rollover_cost / b.price) * 10000) : 0;
                return this.currentSortAsc ? valA - valB : valB - valA;
            });
        } else {
            displayData.sort((a, b) => {
                let valA = a[this.currentSortCol];
                let valB = b[this.currentSortCol];

                if (typeof valA === 'string') valA = valA.toUpperCase();
                if (typeof valB === 'string') valB = valB.toUpperCase();

                if (valA < valB) return this.currentSortAsc ? -1 : 1;
                if (valA > valB) return this.currentSortAsc ? 1 : -1;
                return 0;
            });
        }

        // Render Table
        const tbody = document.getElementById('rollover-analysis-body');
        tbody.innerHTML = '';

        if (displayData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; color:#888;">No F&O stocks found.</td></tr>';
        } else {
            let html = '';
            displayData.forEach(d => {
                let costColor = d.rollover_cost >= 0 ? '#60a5fa' : '#ff4d4d';
                let rollColor = '#ff9800'; // Orange to match charts
                let pColor = d.price_chg_pct >= 0 ? '#60a5fa' : '#ff4d4d';
                let oColor = d.oi_chg_pct >= 0 ? '#60a5fa' : '#ff4d4d';
                let bps = (d.price && d.price > 0) ? ((d.rollover_cost / d.price) * 10000) : 0;

                html += `
                <tr class="roll-row" onclick="RolloverTool.toggleHistory('${d.symbol}')" style="cursor: pointer; border-bottom: 1px solid #333; transition: background 0.2s;" onmouseover="this.style.background='#2a2a2a'" onmouseout="this.style.background='transparent'">
                    <td style="padding: 10px 8px; text-align: center; width: 30px;"><span id="roll-icon-${d.symbol}" style="font-size: 14px; color: #00bcd4; font-weight: bold;">▶</span></td>
                    <td style="padding: 10px 8px;"><b>${d.symbol}</b></td>
                    <td style="padding: 10px 8px; color: #aaa;">${d.date || d.history?.[0]?.date || '-'} (Latest)</td>
                    <td style="padding: 10px 8px; color: ${rollColor}; font-weight: bold;">${(d.rollover_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; color: ${costColor};">${(d.rollover_cost||0).toFixed(2)}</td>
                    <td style="padding: 10px 8px; color: #ffffff;">${bps.toFixed(1)}</td>
                    <td style="padding: 10px 8px; color: ${costColor};">${(d.rollover_cost_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; color: #ffffff;">${(d.price||0).toFixed(2)}</td>
                    <td style="padding: 10px 8px; color: ${pColor};">${(d.price_chg_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; color: #ccc;">${(d.total_oi||0).toLocaleString()}</td>
                    <td style="padding: 10px 8px; color: ${oColor};">${(d.oi_chg_pct||0).toFixed(2)}%</td>
                </tr>`;

                if (d.history && d.history.length > 1) {
                    d.history.slice(1).forEach((h, idx) => {
                        let hpColor = h.price_chg_pct >= 0 ? '#60a5fa' : '#ff4d4d';
                        let hoColor = h.oi_chg_pct >= 0 ? '#60a5fa' : '#ff4d4d';
                        let rowBg = '#151515';
                        let hCostColor = h.rollover_cost >= 0 ? '#60a5fa' : '#ff4d4d';
                        let hBps = (h.price && h.price > 0) ? ((h.rollover_cost / h.price) * 10000) : 0;
                        let hRollColor = '#ff9800'; // Orange
                        // Matching exact columns: [Icon, Symbol/Date, Rollover %, Spread, BPS, Cost %, FUT Price, Price Chg %, Total OI, OI Chg %]
                        html += `<tr class="roll-history-row-${d.symbol}" style="background: ${rowBg}; border-bottom: 1px solid #222; font-size: 0.85em; display: none;">
                            <td style="padding: 6px 8px; width: 30px; border-right: 1px solid #333;"></td>
                            <td style="padding: 6px 8px;"></td>
                            <td style="padding: 6px 8px; color: #888;">└ ${h.date}</td>
                            <td style="padding: 6px 8px; color: ${hRollColor};">${(h.rollover_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 8px; color: ${hCostColor};">${(h.rollover_cost || 0).toFixed(2)}</td>
                            <td style="padding: 6px 8px; color: #ffffff;">${hBps.toFixed(1)}</td>
                            <td style="padding: 6px 8px; color: ${hCostColor};">${(h.rollover_cost_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 8px; color: #ffffff;">${(h.price || 0).toFixed(2)}</td>
                            <td style="padding: 6px 8px; color: ${hpColor};">${(h.price_chg_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 8px;">${(h.oi || 0).toLocaleString()}</td>
                            <td style="padding: 6px 8px; color: ${hoColor};">${(h.oi_chg_pct || 0).toFixed(2)}%</td>
                        </tr>`;
                    });
                }
            });
            tbody.innerHTML = html;
        }

    },

    sortData: function(col) {
        if (!document.getElementById('rollover-analysis-body')) return;

        if (this.currentSortCol === col) {
            this.currentSortAsc = !this.currentSortAsc;
        } else {
            this.currentSortCol = col;
            this.currentSortAsc = true;
        }

        // Custom sorting for calculated BPS
        if (col === 'bps') {
            this.aggregatedData.sort((a, b) => {
                let valA = (a.price && a.price > 0) ? ((a.rollover_cost / a.price) * 10000) : 0;
                let valB = (b.price && b.price > 0) ? ((b.rollover_cost / b.price) * 10000) : 0;
                return this.currentSortAsc ? valA - valB : valB - valA;
            });
        }

        this.renderAggregatedView();
    },

    updateDynamicChart: async function() {
        const sectorSelector = document.getElementById('rollover-chart-sector-filter');
        const stockSelector = document.getElementById('rollover-chart-stock-filter');
        const chartDom = document.getElementById('rollover-dynamic-chart');

        if (!sectorSelector || !stockSelector || !chartDom) return;

        const selectedSector = sectorSelector.value;
        const selectedStock = stockSelector.value;

        if (window.rolloverDynamicChartInstance) {
            window.rolloverDynamicChartInstance.dispose();
        }
        window.rolloverDynamicChartInstance = echarts.init(chartDom);

        try {
            if (selectedSector === 'ALL') {
                // Show current expiry rollover for all sectors
                stockSelector.style.display = 'none';

                // We can calculate this from this.allData locally
                const sectorAverages = {};
                this.allData.forEach(d => {
                    if (d.sector && d.sector !== 'Unknown') {
                        if (!sectorAverages[d.sector]) sectorAverages[d.sector] = { sum: 0, count: 0 };
                        sectorAverages[d.sector].sum += d.rollover_pct;
                        sectorAverages[d.sector].count += 1;
                    }
                });

                const sectors = Object.keys(sectorAverages).sort();
                const values = sectors.map(s => (sectorAverages[s].sum / sectorAverages[s].count).toFixed(2));

                const option = {
                    title: { text: 'Current Avg Rollover by Sector', textStyle: { color: '#ccc', fontSize: 14 }, left: 'center', top: 10 },
                    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                    grid: { left: '3%', right: '4%', bottom: '15%', top: '20%', containLabel: true },
                    xAxis: { type: 'category', data: sectors, axisLabel: { color: '#ccc', rotate: 45, interval: 0, fontSize: 10 } },
                    yAxis: { type: 'value', axisLabel: { color: '#ccc', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#333' } } },
                    series: [{
                        name: 'Avg Rollover',
                        type: 'bar',
                        itemStyle: { color: '#ff9800' }, // Orange
                        data: values,
                        label: { show: true, position: 'top', color: '#ccc', formatter: '{c}%', fontSize: 9 }
                    }]
                };
                window.rolloverDynamicChartInstance.setOption(option);

            } else {
                // A specific sector is selected. Populate stock dropdown.
                stockSelector.style.display = 'inline-block';

                const sectorStocks = this.allData.filter(d => d.sector === selectedSector).sort((a,b) => a.symbol.localeCompare(b.symbol));

                // Repopulate stock dropdown if it doesn't match current sector
                if (stockSelector.getAttribute('data-sector') !== selectedSector) {
                    stockSelector.innerHTML = '<option value="">Select Stock</option>';
                    sectorStocks.forEach(s => {
                        stockSelector.innerHTML += `<option value="${s.symbol}">${s.symbol}</option>`;
                    });
                    stockSelector.setAttribute('data-sector', selectedSector);
                    stockSelector.value = ''; // Reset stock selection
                }

                if (!selectedStock) {
                    // Show stocks in the sector
                    const symbols = sectorStocks.map(s => s.symbol);
                    const values = sectorStocks.map(s => s.rollover_pct);

                    const option = {
                        title: { text: `${selectedSector} Stocks Rollover`, textStyle: { color: '#ccc', fontSize: 14 }, left: 'center', top: 10 },
                        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                        grid: { left: '3%', right: '4%', bottom: '15%', top: '20%', containLabel: true },
                        xAxis: { type: 'category', data: symbols, axisLabel: { color: '#ccc', rotate: 45, interval: 0, fontSize: 10 } },
                        yAxis: { type: 'value', axisLabel: { color: '#ccc', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#333' } } },
                        series: [{
                            name: 'Rollover',
                            type: 'bar',
                            itemStyle: { color: '#ff9800' }, // Orange
                            data: values,
                            label: { show: true, position: 'top', color: '#ccc', formatter: '{c}%', fontSize: 9 }
                        }]
                    };
                    window.rolloverDynamicChartInstance.setOption(option);
                } else {
                    // Fetch 24-month history for the stock
                    window.rolloverDynamicChartInstance.showLoading({ text: 'Loading 24M History...', color: '#00bcd4', textColor: '#ccc', maskColor: 'rgba(0, 0, 0, 0.5)' });

                    // Determine if we should load expiry-only or daily history based on a hypothetical checkbox or just default to expiry_only for "24 Month History"
                    // Since the user requested "expiry to expiry rollover for last 12 months" when checking a box, let's add that logic
                    const isMoM = document.getElementById('rollover-mom-checkbox') ? document.getElementById('rollover-mom-checkbox').checked : false;

                    const res = await fetch(`/api/data/analysis/rollover/history/${selectedStock}?expiry_only=${isMoM}`);
                    if (!res.ok) throw new Error("Failed to load history");
                    const responseJson = await res.json();

                    window.rolloverDynamicChartInstance.hideLoading();

                    const data = Array.isArray(responseJson) ? responseJson : (responseJson.data || []);

                    const expiries = data.map(d => d.date || d.expiry).reverse();
                    const values = data.map(d => d.rollover_pct).reverse();
                    const spreads = data.map(d => d.rollover_cost || 0).reverse();

                    const titleText = isMoM ? `${selectedStock} - Month-on-Month Rollover History` : `${selectedStock} - Daily Rollover History`;

                    const option = {
                        title: { text: titleText, textStyle: { color: '#ccc', fontSize: 14 }, left: 'center', top: 10 },
                        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                        legend: { data: ['Rollover %', 'Spread'], top: 30, textStyle: { color: '#ccc' } },
                        grid: { left: '5%', right: '5%', bottom: '15%', top: '25%', containLabel: true },
                        xAxis: { type: 'category', data: expiries, axisLabel: { color: '#ccc', rotate: 45, interval: 0, fontSize: 10 } },
                        yAxis: [
                            { type: 'value', name: 'Rollover %', axisLabel: { color: '#ff9800', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#333' } } },
                            { type: 'value', name: 'Spread', position: 'right', axisLabel: { color: '#60a5fa' }, splitLine: { show: false } }
                        ],
                        series: [
                            {
                                name: 'Rollover %',
                                type: 'line',
                                yAxisIndex: 0,
                                symbol: 'circle',
                                symbolSize: 8,
                                itemStyle: { color: '#ff9800' }, // Orange
                                lineStyle: { width: 3 },
                                data: values,
                                label: { show: true, position: 'top', color: '#ccc', formatter: '{c}%', fontSize: 9 }
                            },
                            {
                                name: 'Spread',
                                type: 'bar',
                                yAxisIndex: 1,
                                itemStyle: { color: (params) => params.value >= 0 ? '#60a5fa' : '#ff4d4d' }, // Blue positive, Red negative
                                data: spreads,
                                label: { show: true, position: 'inside', color: '#fff', formatter: '{c}', fontSize: 9 }
                            }
                        ]
                    };
                    window.rolloverDynamicChartInstance.setOption(option);
                }
            }
            window.addEventListener('resize', () => window.rolloverDynamicChartInstance.resize());
        } catch (e) {
             if (window.rolloverDynamicChartInstance) window.rolloverDynamicChartInstance.hideLoading();
             chartDom.innerHTML = `<p style="color:red; text-align:center; padding-top:50px;">Error: ${e.message}</p>`;
        }
    },


    toggleHistory: function(symbol) {
        const histRows = document.querySelectorAll(`.roll-history-row-${symbol}`);
        const icon = document.getElementById(`roll-icon-${symbol}`);
        if (!histRows || histRows.length === 0) return;

        let isHidden = histRows[0].style.display === 'none' || histRows[0].style.display === '';

        histRows.forEach(row => {
            row.style.display = isHidden ? 'table-row' : 'none';
        });

        if (icon) {
            icon.innerText = isHidden ? '▼' : '▶';
        }
    },

    filterData: function() {
        if (!document.getElementById('rollover-analysis-body')) return;
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
                        <div style="font-size: 1.5em; color: #60a5fa; font-weight: bold;">${data.rollover_pct}%</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; color: #888;">Rollover Cost (Spread)</div>
                        <div style="font-size: 1.5em; color: ${data.rollover_cost >= 0 ? '#60a5fa' : '#ff4d4d'};">${data.rollover_cost} (${data.rollover_cost_pct}%)</div>
                    </div>
                </div>

                <table style="width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 0.9em; text-align: left;">
                    <thead>
                        <tr style="position: sticky; top: 0; background: #222; z-index: 10; border-bottom: 2px solid #00bcd4;">
                            <th style="padding: 8px;">Month</th>
                            <th style="padding: 8px;">Expiry</th>
                            <th style="padding: 8px;">Price</th>
                            <th style="padding: 8px;">OI</th>
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

                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 20px;">
                    <h4 style="margin: 0; color: #fff;" id="single-symbol-history-title">24-Month Rollover History</h4>
                    <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="if(window.rolloverMomChartInstance) exportChartDataToExcel(window.rolloverMomChartInstance, 'Rollover_History_${symbol}');"><i class="fas fa-download"></i> Excel</button>
                </div>
                <div id="rollover-mom-history-chart" style="width: 100%; height: 250px; margin-top: 10px;"></div>
                <div id="rollover-mom-history-table-container"></div>
                <p style="color: #888; font-size: 0.85em; margin-top: 15px;">To return to the all F&O view, clear the search and click "Refresh All".</p>
            </div>`;

            detailsDiv.innerHTML = html;

            // Fetch and render MoM history inline
            const momCheckbox = document.getElementById('rollover-mom-checkbox');
            const isMoM = momCheckbox ? momCheckbox.checked : false;

            const titleEl = document.getElementById('single-symbol-history-title');
            if (titleEl) {
                titleEl.innerText = isMoM ? 'Month-on-Month Rollover History' : 'Daily Rollover History';
            }

            const histRes = await fetch(`/api/data/analysis/rollover/history/${symbol}?expiry_only=${isMoM}`);
            if (histRes.ok) {
                const histDataResp = await histRes.json();
                const histData = Array.isArray(histDataResp) ? histDataResp : (histDataResp.data || []);
                if (histData.length > 0) {
                    const expiries = histData.map(d => d.date || d.expiry).reverse();
                        const values = histData.map(d => d.rollover_pct).reverse();
                        const spreads = histData.map(d => d.rollover_cost || 0).reverse();
                        const bpsValues = histData.map(d => {
                            const fPrice = d.price !== undefined ? d.price : d.fut_price;
                            if (d.rollover_cost !== null && fPrice !== null && fPrice > 0) {
                                return ((d.rollover_cost / fPrice) * 10000).toFixed(1);
                            }
                            return "-";
                        }).reverse();

                    // Render Chart
                    const momChartDom = document.getElementById('rollover-mom-history-chart');
                    if (window.rolloverMomChartInstance) window.rolloverMomChartInstance.dispose();
                    window.rolloverMomChartInstance = echarts.init(momChartDom);
                    window.rolloverMomChartInstance.setOption({
                        backgroundColor: 'transparent',
                        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                        legend: { data: ['Rollover %', 'Spread'], top: 0, textStyle: { color: '#ccc' } },
                        grid: { left: '3%', right: '3%', bottom: '15%', top: '15%', containLabel: true },
                        xAxis: { type: 'category', data: expiries, axisLabel: { color: '#888', fontSize: 10 } },
                        yAxis: [
                            { type: 'value', name: 'Rollover %', axisLabel: { color: '#ff9800', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#333', type: 'dashed' } } },
                            { type: 'value', name: 'Spread', position: 'right', axisLabel: { color: '#60a5fa' }, splitLine: { show: false } }
                        ],
                        series: [
                            {
                                name: 'Rollover %',
                                type: 'line',
                                yAxisIndex: 0,
                                symbol: 'circle',
                                symbolSize: 6,
                                itemStyle: { color: '#ff9800' }, // Orange
                                lineStyle: { width: 2 },
                                data: values,
                                label: { show: true, position: 'top', color: '#ccc', formatter: '{c}%', fontSize: 9 }
                            },
                            {
                                name: 'Spread',
                                type: 'bar',
                                yAxisIndex: 1,
                                itemStyle: { color: (params) => params.value >= 0 ? '#60a5fa' : '#ff4d4d' }, // Blue positive, Red negative
                                data: spreads,
                                label: { show: true, position: 'inside', color: '#fff', formatter: '{c}', fontSize: 9 }
                            }
                        ]
                    });

                    // Render small table
                    let histTableHtml = `<table style="width: 100%; margin-top: 10px; border-collapse: collapse; font-size: 0.85em; text-align: center;">
                            <thead style="background: #333;"><tr>`;
                        expiries.forEach(e => histTableHtml += `<th style="padding: 4px; color: #aaa;">${e}<br><span style="font-size:9px; color:#aaa;">Roll% | Spread | BPS</span></th>`);
                        histTableHtml += `</tr></thead><tbody><tr>`;
                        values.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: #ff9800;">${v !== null && v !== undefined ? v + '%' : '-'}</td>`);
                        histTableHtml += `</tr><tr>`;
                        spreads.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: ${v >= 0 ? '#60a5fa' : '#ff4d4d'};">${v}</td>`);
                        histTableHtml += `</tr><tr>`;
                        bpsValues.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: #ffffff;">${v}</td>`);
                        histTableHtml += `</tr></tbody></table>`;
                    document.getElementById('rollover-mom-history-table-container').innerHTML = histTableHtml;
                } else {
                    document.getElementById('rollover-mom-history-chart').innerHTML = `<p style="color:#888;">No historical data available.</p>`;
                }
            }
            // Also filter the table to just this symbol
            this.filterData();

        } catch (e) {
            detailsDiv.innerHTML = `<p style="color: red; text-align:center; margin-top: 20px;">Error: ${e.message}</p>`;
        }
    },

    handleTick: function(tick) {
        // Update
    },

    exportMatrixExcel: function() {
        const matrixContainer = document.getElementById('rollover-matrix-container');
        if (!matrixContainer || matrixContainer.style.display === 'none') {
            alert("Matrix data not available.");
            return;
        }
        const table = matrixContainer.querySelector('table');
        if (!table) return;

        const dataArray = [];

        // Headers
        const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());
        dataArray.push(headers);

        // Rows
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const cols = Array.from(row.querySelectorAll('td')).map(td => td.innerText.trim());
            dataArray.push(cols);
        });

        const filename = "rollover_history_matrix";

        if (typeof XLSX !== 'undefined') {
            try {
                const ws = XLSX.utils.aoa_to_sheet(dataArray);
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, "Matrix");
                XLSX.writeFile(wb, `${filename}.xlsx`);
                return;
            } catch (e) {
                console.error("Error exporting to Excel:", e);
            }
        }

        console.warn("XLSX library not loaded or failed. Falling back to CSV.");
        let csvContent = dataArray.map(row => row.map(v => `"${v.replace(/"/g, '""')}"`).join(",")).join("\n");
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `${filename}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    renderMatrix: function(data, isMoM) {
        const container = document.getElementById('rollover-matrix-container');
        if (!container) return;

        if (!data || data.length === 0) {
            container.innerHTML = '<p style="text-align:center; color:#888; padding: 20px;">No historical matrix data available.</p>';
            return;
        }

        // Extract all unique dates from the history of all stocks
        const dateSet = new Set();
        data.forEach(item => {
            if (item.history && Array.isArray(item.history)) {
                item.history.forEach(h => dateSet.add(h.date));
            }
        });

        // Sort dates descending
        const dates = Array.from(dateSet).sort((a, b) => new Date(b) - new Date(a));

        if (dates.length === 0) {
            container.innerHTML = '<p style="padding: 10px; color:#888;">No history available to build matrix.</p>';
            return;
        }

        // Limit to 24 columns max to match the 24-month requirement visually without overflowing excessively
        const displayDates = dates.slice(0, 24);

        let tableHtml = `
            <table class="table table-bordered table-hover" style="font-size: 11px; white-space: nowrap; margin-bottom: 0; border-collapse: collapse; width: 100%;">
                <thead style="position: sticky; top: 0; background: #222; z-index: 2; border-bottom: 2px solid #555;">
                    <tr>
                        <th style="position: sticky; left: 0; background: #222; z-index: 3; border: 1px solid #444; padding: 6px 10px;">Symbol</th>
                        <th style="position: sticky; left: 80px; background: #222; z-index: 3; border: 1px solid #444; padding: 6px 10px;">Metric</th>
                        ${displayDates.map(date => `<th style="text-align: center; border: 1px solid #444; padding: 6px;">${date}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
        `;

        // Sort data by symbol alphabetically
        const sortedData = [...data].sort((a, b) => a.symbol.localeCompare(b.symbol));

        sortedData.forEach(item => {
            const histMap = {};
            if (item.history) {
                item.history.forEach(h => {
                    histMap[h.date] = h;
                });
            }

            const clickHandler = `document.getElementById('rollover-symbol').value='${item.symbol}'; RolloverTool.analyzeSingle(); window.scrollTo(0,0);`;

            // Row 1: Roll %
            tableHtml += `<tr style="cursor: pointer;" onclick="${clickHandler}">`;
            tableHtml += `<td rowspan="3" style="position: sticky; left: 0; background: #2a2a2a; color: #64b5f6; font-weight: bold; z-index: 1; vertical-align: middle; border: 1px solid #444; border-bottom: 2px solid #555; padding: 4px 10px;">${item.symbol}</td>`;
            tableHtml += `<td style="position: sticky; left: 80px; background: #2a2a2a; color: #ccc; z-index: 1; border: 1px solid #444; padding: 4px 10px;">Roll %</td>`;

            displayDates.forEach(date => {
                const h = histMap[date];
                if (h && h.rollover_pct !== null && h.rollover_pct !== undefined) {
                    tableHtml += `<td style="text-align: center; color: #ff9800; border: 1px solid #444; padding: 4px;">${h.rollover_pct.toFixed(1)}%</td>`;
                } else {
                    tableHtml += `<td style="text-align: center; color: #555; border: 1px solid #444; padding: 4px;">-</td>`;
                }
            });
            tableHtml += `</tr>`;

            // Row 2: Spread
            tableHtml += `<tr style="cursor: pointer;" onclick="${clickHandler}">`;
            tableHtml += `<td style="position: sticky; left: 80px; background: #2a2a2a; color: #ccc; z-index: 1; border: 1px solid #444; padding: 4px 10px;">Spread</td>`;
            displayDates.forEach(date => {
                const h = histMap[date];
                if (h && h.rollover_cost !== null && h.rollover_cost !== undefined) {
                    const color = h.rollover_cost >= 0 ? '#60a5fa' : '#ff4d4d';
                    tableHtml += `<td style="text-align: center; color: ${color}; border: 1px solid #444; padding: 4px;">${h.rollover_cost.toFixed(2)}</td>`;
                } else {
                    tableHtml += `<td style="text-align: center; color: #555; border: 1px solid #444; padding: 4px;">-</td>`;
                }
            });
            tableHtml += `</tr>`;

            // Row 3: BPS
            tableHtml += `<tr style="cursor: pointer;" onclick="${clickHandler}">`;
            tableHtml += `<td style="position: sticky; left: 80px; background: #2a2a2a; color: #ccc; z-index: 1; border: 1px solid #444; border-bottom: 2px solid #555; padding: 4px 10px;">BPS</td>`;
            displayDates.forEach(date => {
                const h = histMap[date];
                const hPrice = h ? (h.price !== undefined ? h.price : h.fut_price) : null;
                if (h && h.rollover_cost !== null && hPrice !== null && hPrice > 0) {
                    const bps = ((h.rollover_cost / hPrice) * 10000).toFixed(1);
                    tableHtml += `<td style="text-align: center; color: #ffffff; border: 1px solid #444; border-bottom: 2px solid #555; padding: 4px;">${bps}</td>`;
                } else {
                    tableHtml += `<td style="text-align: center; color: #555; border: 1px solid #444; border-bottom: 2px solid #555; padding: 4px;">-</td>`;
                }
            });
            tableHtml += `</tr>`;
        });

        tableHtml += `</tbody></table>`;
        container.innerHTML = tableHtml;
    }
};


// Register
window.addEventListener('load', () => {
   if (window.WorkbookManager) {
       window.WorkbookManager.modules['rollover'] = RolloverTool;
   }
});
