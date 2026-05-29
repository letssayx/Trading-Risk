import re

with open('./backend/ui/static/js/rolloverTool.js', 'r') as f:
    content = f.read()

# 1. Update init to set NIFTY and load single
init_search = """    init: function() {
        const container = document.getElementById(this.containerId);
        if (container && !container.innerHTML.includes('rollover-symbol')) {
            this.render(container);
            this.loadAggregatedData();
        }
    },"""

init_replace = """    init: function() {
        const container = document.getElementById(this.containerId);
        if (container && !container.innerHTML.includes('rollover-symbol')) {
            this.render(container);

            const symInput = document.getElementById('rollover-symbol');
            if (symInput && !symInput.value.trim()) {
                symInput.value = 'NIFTY';
            }

            this.loadAggregatedData();
            this.analyzeSingle();
        }
    },"""

content = content.replace(init_search, init_replace)


# 2. Update render string to include the single details div permanently at the top and the matrix below it
render_search = """                    <div style="display: flex; gap: 10px; align-items: center; margin-left: 20px; border-left: 1px solid #444; padding-left: 15px;">
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;">
                            <input type="checkbox" id="rollover-force-sync"> Force
                        </label>
                        <button onclick="RolloverTool.syncAndLoadAggregatedData(document.getElementById('rollover-force-sync').checked)" class="btn btn-primary" style="display: flex; align-items: center; gap: 5px;">
                            <i class="fas fa-sync-alt"></i> Refresh All
                        </button>
                    </div>

                </div>

                <div id="rollover-results" style="flex-grow: 1; display: flex; flex-direction: column; overflow: hidden;">
                    <!-- Aggregated View will render here -->
                </div>"""

render_replace = """                    <div style="display: flex; gap: 10px; align-items: center; margin-left: 20px; border-left: 1px solid #444; padding-left: 15px;">
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;">
                            <input type="checkbox" id="rollover-force-sync"> Force
                        </label>
                        <button onclick="RolloverTool.syncAndLoadAggregatedData(document.getElementById('rollover-force-sync').checked)" class="btn btn-primary" style="display: flex; align-items: center; gap: 5px;">
                            <i class="fas fa-sync-alt"></i> Refresh All
                        </button>
                    </div>

                </div>

                <!-- Permanent Single Details Top View -->
                <div id="rollover-single-details" style="display: none; background: #2a2a2a; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <p style="text-align:center; color:#888;">Loading Default Symbol Details...</p>
                </div>

                <!-- 24-Month All Stocks Matrix View -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <h3 style="margin: 0; color: #fff; font-size: 14px; font-weight: bold;">24-Month All Stocks History Matrix</h3>
                    <button onclick="RolloverTool.exportMatrixCSV()" class="btn btn-sm btn-secondary" style="padding: 2px 8px; font-size: 11px;">
                        <i class="fas fa-download"></i> CSV
                    </button>
                </div>
                <div style="width: 100%; border-bottom: 1px solid #444; margin-bottom: 10px;"></div>

                <div id="rollover-matrix-container" style="max-height: 400px; overflow-y: auto; margin-bottom: 20px; border: 1px solid #444; border-radius: 4px; display: none;">
                    <!-- Matrix Table will render here -->
                </div>

                <div id="rollover-results" style="flex-grow: 1; display: flex; flex-direction: column; overflow: hidden;">
                    <!-- Aggregated View will render here -->
                </div>"""

content = content.replace(render_search, render_replace)

# 3. Modify `loadAggregatedData` to call renderMatrix
load_aggr_search = """            this.allData = data.data || [];
            this.currentSortCol = 'rollover_pct';
            this.currentSortAsc = false;
            this.renderAggregatedView();"""

load_aggr_replace = """            this.allData = data.data || [];
            this.currentSortCol = 'rollover_pct';
            this.currentSortAsc = false;
            this.renderAggregatedView();

            const momCheckbox = document.getElementById('rollover-mom-checkbox');
            const isMoM = momCheckbox ? momCheckbox.checked : false;
            this.renderMatrix(this.allData, isMoM);"""

content = content.replace(load_aggr_search, load_aggr_replace)


# 4. Modify single view to remove creating detailsDiv dynamically and calculate BPS
single_search = """        const symbol = document.getElementById('rollover-symbol').value.toUpperCase().trim();
        const resultsDiv = document.getElementById('rollover-results');

        if (!symbol) return;

        // Create or clear single details container
        let detailsDiv = document.getElementById('rollover-single-details');
        if (!detailsDiv) {
            detailsDiv = document.createElement('div');
            detailsDiv.id = 'rollover-single-details';
            detailsDiv.style.cssText = 'background: #2a2a2a; padding: 15px; border-radius: 5px; margin-bottom: 20px;';
            resultsDiv.parentNode.insertBefore(detailsDiv, resultsDiv);
        }

        detailsDiv.innerHTML = '<p style="text-align:center; color:#888;">Loading Single Symbol Details...</p>';"""

single_replace = """        const symbol = document.getElementById('rollover-symbol').value.toUpperCase().trim();
        let detailsDiv = document.getElementById('rollover-single-details');
        const resultsDiv = document.getElementById('rollover-results');

        if (!symbol) return;

        if (!detailsDiv) return;
        detailsDiv.style.display = 'block';

        if (detailsDiv.innerHTML.indexOf('Loading') === -1 && !detailsDiv.innerHTML.includes(symbol)) {
            detailsDiv.innerHTML = '<p style="text-align:center; color:#888; margin-top: 20px;">Loading Single Symbol Details...</p>';
        }"""

content = content.replace(single_search, single_replace)

# 5. Fix BPS in Single Stats
single_stats_search = """            let statsHtml = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div style="background: #333; padding: 10px; border-radius: 5px; text-align: center;">
                        <div style="font-size: 12px; color: #aaa;">Current Rollover %</div>
                        <div style="font-size: 18px; color: #fff; font-weight: bold;">${latestData.rollover_pct !== null ? latestData.rollover_pct.toFixed(2) + '%' : '--'}</div>
                    </div>
                    <div style="background: #333; padding: 10px; border-radius: 5px; text-align: center;">
                        <div style="font-size: 12px; color: #aaa;">Current Spread (Pts)</div>
                        <div style="font-size: 18px; color: #fff; font-weight: bold;">${latestData.rollover_cost !== null ? latestData.rollover_cost.toFixed(2) : '--'}</div>
                    </div>
                    <div style="background: #333; padding: 10px; border-radius: 5px; text-align: center;">
                        <div style="font-size: 12px; color: #aaa;">Current Cost %</div>
                        <div style="font-size: 18px; color: #fff; font-weight: bold;">${latestData.rollover_cost_pct !== null ? latestData.rollover_cost_pct.toFixed(2) + '%' : '--'}</div>
                    </div>
                </div>
            `;"""

single_stats_replace = """            let bps = '--';
            if (latestData.rollover_cost !== null && latestData.fut_price !== null && latestData.fut_price > 0) {
                bps = ((latestData.rollover_cost / latestData.fut_price) * 10000).toFixed(2);
            }

            let statsHtml = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div style="background: #333; padding: 10px; border-radius: 5px; text-align: center;">
                        <div style="font-size: 12px; color: #aaa;">Current Rollover %</div>
                        <div style="font-size: 18px; color: #fff; font-weight: bold;">${latestData.rollover_pct !== null ? latestData.rollover_pct.toFixed(2) + '%' : '--'}</div>
                    </div>
                    <div style="background: #333; padding: 10px; border-radius: 5px; text-align: center;">
                        <div style="font-size: 12px; color: #aaa;">Current Spread (Pts)</div>
                        <div style="font-size: 18px; color: #fff; font-weight: bold;">${latestData.rollover_cost !== null ? latestData.rollover_cost.toFixed(2) : '--'}</div>
                    </div>
                    <div style="background: #333; padding: 10px; border-radius: 5px; text-align: center;">
                        <div style="font-size: 12px; color: #aaa;">Spread BPS</div>
                        <div style="font-size: 18px; color: #fff; font-weight: bold;">${bps}</div>
                    </div>
                    <div style="background: #333; padding: 10px; border-radius: 5px; text-align: center;">
                        <div style="font-size: 12px; color: #aaa;">Current Cost %</div>
                        <div style="font-size: 18px; color: #fff; font-weight: bold;">${latestData.rollover_cost_pct !== null ? latestData.rollover_cost_pct.toFixed(2) + '%' : '--'}</div>
                    </div>
                </div>
            `;"""
content = content.replace(single_stats_search, single_stats_replace)


# 6. Remove the small history table rendering inside `analyzeSingle` so it only shows the chart
remove_table_search = """            detailsDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: #fff; font-size: 16px;">${symbol} - Rollover Details</h3>
                    <button onclick="document.getElementById('rollover-single-details').remove()" class="btn btn-sm btn-secondary">✖ Close</button>
                </div>
                ${statsHtml}
                <div id="rollover-mom-history-chart" style="width: 100%; height: 250px; margin-top: 10px;"></div>
                <div style="margin-top: 20px; max-height: 250px; overflow-y: auto;">
                    <table class="table" style="font-size: 12px;">
                        <thead style="position: sticky; top: 0; background: #222;">
                            <tr>
                                <th>Date</th>
                                <th>Rollover %</th>
                                <th>Spread</th>
                                <th>Cost %</th>
                                <th>Fut Price</th>
                                <th>Total OI</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${histData.map(d => `
                                <tr>
                                    <td>${d.date}</td>
                                    <td>${d.rollover_pct !== null ? d.rollover_pct.toFixed(2)+'%' : '--'}</td>
                                    <td>${d.rollover_cost !== null ? d.rollover_cost.toFixed(2) : '--'}</td>
                                    <td>${d.rollover_cost_pct !== null ? d.rollover_cost_pct.toFixed(2)+'%' : '--'}</td>
                                    <td>${d.fut_price !== null ? d.fut_price.toFixed(2) : '--'}</td>
                                    <td>${d.total_oi !== null ? d.total_oi.toLocaleString() : '--'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;"""

remove_table_replace = """            detailsDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: #ff9800; font-size: 16px;">${symbol} - Detailed Analysis</h3>
                </div>
                ${statsHtml}
                <div id="rollover-mom-history-chart" style="width: 100%; height: 250px; margin-top: 10px;"></div>
            `;"""

content = content.replace(remove_table_search, remove_table_replace)


# 7. Make rows in the Aggregated table clickable to load the single view
aggr_row_search = """                <tr style="cursor: pointer;">
                    <td style="color: #64b5f6; font-weight: bold;">${item.symbol}</td>"""

aggr_row_replace = """                <tr style="cursor: pointer;" onclick="document.getElementById('rollover-symbol').value='${item.symbol}'; RolloverTool.analyzeSingle(); window.scrollTo(0,0);">
                    <td style="color: #64b5f6; font-weight: bold;">${item.symbol}</td>"""

content = content.replace(aggr_row_search, aggr_row_replace)


# 8. Add `renderMatrix` and `exportMatrixCSV` methods to RolloverTool
methods_to_add = """
    exportMatrixCSV: function() {
        const matrixContainer = document.getElementById('rollover-matrix-container');
        if (!matrixContainer || matrixContainer.style.display === 'none') {
            alert("Matrix data not available.");
            return;
        }
        const table = matrixContainer.querySelector('table');
        if (!table) return;

        let csvContent = "data:text/csv;charset=utf-8,";

        // Headers
        const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText);
        csvContent += headers.join(",") + "\\n";

        // Rows
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const cols = Array.from(row.querySelectorAll('td')).map(td => td.innerText.replace(/,/g, ''));
            csvContent += cols.join(",") + "\\n";
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `rollover_history_matrix.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    renderMatrix: function(data, isMoM) {
        const container = document.getElementById('rollover-matrix-container');
        if (!container) return;

        if (!data || data.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'block';

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
            <table class="table table-bordered table-hover" style="font-size: 11px; white-space: nowrap; margin-bottom: 0;">
                <thead style="position: sticky; top: 0; background: #222; z-index: 2;">
                    <tr>
                        <th style="position: sticky; left: 0; background: #222; z-index: 3;">Symbol</th>
                        ${displayDates.map(date => `<th style="text-align: center;">${date}<br><span style="font-size:9px; color:#aaa;">Roll% | Spread | BPS</span></th>`).join('')}
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

            tableHtml += `<tr style="cursor: pointer;" onclick="document.getElementById('rollover-symbol').value='${item.symbol}'; RolloverTool.analyzeSingle(); window.scrollTo(0,0);">`;
            tableHtml += `<td style="position: sticky; left: 0; background: #2a2a2a; color: #64b5f6; font-weight: bold; z-index: 1;">${item.symbol}</td>`;

            displayDates.forEach(date => {
                const h = histMap[date];
                if (h) {
                    const roll = h.rollover_pct !== null ? h.rollover_pct.toFixed(1) + '%' : '-';
                    const spread = h.rollover_cost !== null ? h.rollover_cost.toFixed(2) : '-';

                    let bps = '-';
                    if (h.rollover_cost !== null && h.fut_price !== null && h.fut_price > 0) {
                        bps = ((h.rollover_cost / h.fut_price) * 10000).toFixed(1);
                    }

                    tableHtml += `<td style="text-align: center; border-right: 1px solid #444;">
                        <span style="color: #fff;">${roll}</span> <span style="color:#555;">|</span>
                        <span style="color: #bbb;">${spread}</span> <span style="color:#555;">|</span>
                        <span style="color: #ffb74d;">${bps}</span>
                    </td>`;
                } else {
                    tableHtml += `<td style="text-align: center; color: #555; border-right: 1px solid #444;">- | - | -</td>`;
                }
            });

            tableHtml += `</tr>`;
        });

        tableHtml += `</tbody></table>`;
        container.innerHTML = tableHtml;
    }
};
"""

# Insert methods right before the closing brace of the object
content = content.replace("};\n", methods_to_add)

with open('./backend/ui/static/js/rolloverTool.js', 'w') as f:
    f.write(content)
