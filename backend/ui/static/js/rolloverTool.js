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
                    <span id="rollover-date-display" style="color: #888; margin-left: auto;"></span>
                </div>

                <div id="rollover-results" style="flex: 1; overflow: auto; display: flex; flex-direction: column; gap: 20px; padding-bottom: 20px;">
                    <!-- Charts Area -->
                    <div style="display: flex; gap: 20px; height: 300px; flex-shrink: 0; width: 100%;">
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
                                <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="if(window.rolloverDynamicChartInstance) exportChartDataToCSV(window.rolloverDynamicChartInstance, 'Dynamic_Rollover')"><i class="fas fa-download"></i> CSV</button>
                            </div>
                            <div id="rollover-dynamic-chart" style="width: 100%; height: calc(100% - 30px);"></div>
                        </div>
                    </div>

                    <!-- Table Area -->
                    <div style="display: flex; justify-content: flex-end; margin-bottom: 5px;">
                        <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="exportTableToCSV('rollover-analysis-table', 'Rollover_Analysis')"><i class="fas fa-download"></i> CSV</button>
                    </div>
                    <div class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow-x: auto; flex: 1; min-height: 400px; max-height: calc(100vh - 450px); overflow-y: auto;">
                        <table class="data-table" id="rollover-analysis-table" style="width: 100%; table-layout: fixed;">
                            <thead style="position: sticky; top: 0; background: #222; z-index: 10;">
                                <tr>
                                    <th style="padding: 8px; width: 30px;"></th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('symbol')">Symbol ↕</th>
                                    <th style="padding: 8px;">Date</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_pct')">Rollover % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost')">Spread (Pts) ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost_pct')">Cost % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('fut_close')">FUT Price ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('price_chg_pct')">Price Chg % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('total_oi')">Total OI ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('oi_chg_pct')">OI Chg % ↕</th>
                                </tr>
                            </thead>
                            <tbody id="rollover-analysis-body">
                                <tr><td colspan="9" style="text-align:center; color:#888;">Loading Rollover Data...</td></tr>
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

        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#888;">Fetching aggregated F&O Rollover data...</td></tr>';

        try {
            const res = await fetch('/api/data/analysis/rollover');
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
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#888;">No F&O stocks found.</td></tr>';
        } else {
            let html = '';
            displayData.forEach(d => {
                let costColor = d.rollover_cost >= 0 ? '#60a5fa' : '#f44336';
                let rollColor = d.rollover_pct >= 80 ? '#60a5fa' : '#ccc';
                let pColor = d.price_chg_pct >= 0 ? '#60a5fa' : '#f44336';
                let oColor = d.oi_chg_pct >= 0 ? '#60a5fa' : '#f44336';

                html += `
                <tr class="roll-row" onclick="RolloverTool.toggleHistory('${d.symbol}')" style="cursor: pointer; border-bottom: 1px solid #333; transition: background 0.2s;" onmouseover="this.style.background='#2a2a2a'" onmouseout="this.style.background='transparent'">
                    <td style="padding: 10px 8px; text-align: center; width: 30px;"><span id="roll-icon-${d.symbol}" style="font-size: 14px; color: #60a5fa; font-weight: bold;">▶</span></td>
                    <td style="padding: 10px 8px;"><b>${d.symbol}</b></td>
                    <td style="padding: 10px 8px; color: #aaa;">${d.date || d.history?.[0]?.date || '-'} (Latest)</td>
                    <td style="padding: 10px 8px; color: ${rollColor}; font-weight: bold;">${(d.rollover_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; color: ${costColor};">${(d.rollover_cost||0).toFixed(2)}</td>
                    <td style="padding: 10px 8px; color: ${costColor};">${(d.rollover_cost_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; color: #ffffff;">${(d.fut_close||0).toFixed(2)}</td>
                    <td style="padding: 10px 8px; color: ${pColor};">${(d.price_chg_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; color: #ccc;">${(d.total_oi||0).toLocaleString()}</td>
                    <td style="padding: 10px 8px; color: ${oColor};">${(d.oi_chg_pct||0).toFixed(2)}%</td>
                </tr>`;

                if (d.history && d.history.length > 1) {
                    d.history.slice(1, 7).forEach((h, idx) => {
                        let hpColor = h.price_chg_pct >= 0 ? '#60a5fa' : '#f44336';
                        let hoColor = h.oi_chg_pct >= 0 ? '#60a5fa' : '#f44336';
                        let rowBg = '#151515';
                        let hCostColor = h.rollover_cost >= 0 ? '#60a5fa' : '#f44336';
                        // Matching exact columns: [Icon, Symbol/Date, Rollover %, Spread, Cost %, FUT Price, Price Chg %, Total OI, OI Chg %]
                        html += `<tr class="roll-history-row-${d.symbol}" style="background: ${rowBg}; border-bottom: 1px solid #222; font-size: 0.85em; display: none;">
                            <td style="padding: 6px 8px; width: 30px; border-right: 1px solid #333;"></td>
                            <td style="padding: 6px 8px;"></td>
                            <td style="padding: 6px 8px; color: #888;">└ ${h.date}</td>
                            <td style="padding: 6px 8px; color: #60a5fa;">${(h.rollover_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 8px; color: ${hCostColor};">${(h.rollover_cost || 0).toFixed(2)}</td>
                            <td style="padding: 6px 8px; color: ${hCostColor};">${(h.rollover_cost_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 8px; color: #ffffff;">${(h.price || 0).toFixed(2)}</td>
                            <td style="padding: 6px 8px; color: ${hpColor}">${(h.price_chg_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 8px;">${(h.oi || 0).toLocaleString()}</td>
                            <td style="padding: 6px 8px; color: ${hoColor}">${(h.oi_chg_pct || 0).toFixed(2)}%</td>
                        </tr>`;
                    });
                }
            });
            tbody.innerHTML = html;
        }

    },

        sortData: function(col) {
        if (this.currentSortCol === col) {
            this.currentSortAsc = !this.currentSortAsc;
        } else {
            this.currentSortCol = col;
            this.currentSortAsc = true;
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
                        itemStyle: { color: '#E88B1E' }, // Solid Orange
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
                            itemStyle: { color: '#E88B1E' }, // Solid Orange
                            data: values,
                            label: { show: true, position: 'top', color: '#ccc', formatter: '{c}%', fontSize: 9 }
                        }]
                    };
                    window.rolloverDynamicChartInstance.setOption(option);
                } else {
                    // Fetch 12-month history for the stock
                    window.rolloverDynamicChartInstance.showLoading({ text: 'Loading 12M History...', color: '#60a5fa', textColor: '#ccc', maskColor: 'rgba(0, 0, 0, 0.5)' });

                    const res = await fetch(`/api/data/analysis/rollover/history/${selectedStock}`);
                    if (!res.ok) throw new Error("Failed to load history");
                    const responseJson = await res.json();

                    window.rolloverDynamicChartInstance.hideLoading();

                    const data = Array.isArray(responseJson) ? responseJson : (responseJson.data || []);

                    const expiries = data.map(d => d.date || d.expiry).reverse();
                    const values = data.map(d => d.rollover_pct).reverse();

                    const option = {
                        title: { text: `${selectedStock} - 12 Month Rollover History`, textStyle: { color: '#ccc', fontSize: 14 }, left: 'center', top: 10 },
                        tooltip: { trigger: 'axis', formatter: '{b}<br/>Rollover: {c}%' },
                        grid: { left: '3%', right: '4%', bottom: '15%', top: '20%', containLabel: true },
                        xAxis: { type: 'category', data: expiries, axisLabel: { color: '#ccc', rotate: 45, interval: 0, fontSize: 10 } },
                        yAxis: { type: 'value', axisLabel: { color: '#ccc', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#333' } } },
                        series: [{
                            name: 'Rollover',
                            type: 'line',
                            symbol: 'circle',
                            symbolSize: 8,
                            itemStyle: { color: '#E88B1E' }, // Solid Orange
                            lineStyle: { width: 3 },
                            data: values,
                            label: { show: true, position: 'top', color: '#ccc', formatter: '{c}%', fontSize: 9 }
                        }]
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
                        <div style="font-size: 1.5em; color: #60a5fa; font-weight: bold;">${data.rollover_pct}%</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; color: #888;">Rollover Cost (Spread)</div>
                        <div style="font-size: 1.5em; color: ${data.rollover_cost >= 0 ? '#60a5fa' : '#f44336'};">${data.rollover_cost} (${data.rollover_cost_pct}%)</div>
                    </div>
                </div>

                <table style="width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 0.9em; text-align: left;">

                                <thead>
                                    <tr style="position: sticky; top: 0; background: #222; z-index: 10; border-bottom: 2px solid #60a5fa;">
                                        <th style="padding: 8px; width: 30px;"></th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('symbol')">Symbol ↕</th>
                                        <th style="padding: 8px;">Date</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_pct')">Rollover % ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost')">Spread (Pts) ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost_pct')">Cost % ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('fut_close')">FUT Price ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('price_chg_pct')">Price Chg % ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('oi_chg_pct')">OI Chg % ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('total_oi')">Total OI ↕</th>
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
