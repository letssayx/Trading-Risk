import re

with open("backend/ui/static/js/rolloverTool.js", "r") as f:
    js = f.read()

# 1. Update `init` to default to NIFTY
init_old = """        if (container && !container.innerHTML.includes('rollover-symbol')) {
            this.render(container);
            this.loadAggregatedData();
        }"""
init_new = """        if (container && !container.innerHTML.includes('rollover-symbol')) {
            this.render(container);
            const symInput = document.getElementById("rollover-symbol");
            if (symInput && !symInput.value.trim()) {
              symInput.value = "NIFTY";
            }
            this.loadAggregatedData();
            this.analyzeSingle();
        }"""
js = js.replace(init_old, init_new)


# 2. Add exportMatrixCSV and renderMatrix
matrix_funcs = """
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
                    const roll = h.rollover_pct !== null && h.rollover_pct !== undefined ? h.rollover_pct.toFixed(1) + '%' : '-';
                    const spread = h.rollover_cost !== null && h.rollover_cost !== undefined ? h.rollover_cost.toFixed(2) : '-';

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
js = js.replace("};\n\n// Register", matrix_funcs + "\n\n// Register")

# 3. Add Matrix HTML container and fix layout
# In render(), update the #rollover-results innerHTML structure:
results_html_old = """                <div id="rollover-results" style="flex: 1; overflow: auto; display: flex; flex-direction: column; gap: 20px; padding-bottom: 20px;">
                    <!-- Charts Area -->
                    <div style="display: flex; gap: 20px; height: 300px; flex-shrink: 0; width: 100%;">"""

results_html_new = """                <div id="rollover-results" style="flex: 1; overflow: auto; display: flex; flex-direction: column; gap: 20px; padding-bottom: 20px;">
                    <!-- Single Scrip Details -->
                    <div id="rollover-single-details"></div>

                    <!-- Charts Area -->
                    <div style="display: flex; gap: 20px; height: 300px; flex-shrink: 0; width: 100%;">"""
js = js.replace(results_html_old, results_html_new)

matrix_html = """
                    <!-- Matrix Table -->
                    <div style="display: flex; justify-content: flex-end; margin-bottom: -15px;">
                        <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px; margin-right: 15px;" onclick="RolloverTool.exportMatrixCSV()"><i class="fas fa-download"></i> CSV</button>
                    </div>
                    <div id="rollover-matrix-container" class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow-x: auto; flex: 1; min-height: 400px; max-height: calc(100vh - 450px); overflow-y: auto;">
                    </div>
                </div>
"""
js = js.replace('</div>\n                </div>\n            </div>\n        `;', matrix_html + '            </div>\n        `;')

# 4. Do not remove single details div in loadAggregatedData
js = js.replace("""        // Remove single symbol details if present
        const detailsDiv = document.getElementById('rollover-single-details');
        if (detailsDiv) {
            detailsDiv.remove();
        }""", "")

# 5. Add this.renderMatrix in loadAggregatedData
js = js.replace("this.updateDynamicChart();", "this.updateDynamicChart();\n            this.renderMatrix(this.allData, isMoM);")

# 6. Add BPS to analyzeSingle
# We need to replace the data map and the table rendering exactly.
data_map_old = """                        const expiries = histData.map(d => d.date || d.expiry).reverse();
                        const values = histData.map(d => d.rollover_pct).reverse();
                        const spreads = histData.map(d => d.rollover_cost || 0).reverse();"""
data_map_new = """                        const expiries = histData.map(d => d.date || d.expiry).reverse();
                        const values = histData.map(d => d.rollover_pct).reverse();
                        const spreads = histData.map(d => d.rollover_cost || 0).reverse();
                        const bpsValues = histData.map(d => {
                            const fPrice = d.price !== undefined ? d.price : d.fut_price;
                            if (d.rollover_cost !== null && fPrice !== null && fPrice > 0) {
                                return ((d.rollover_cost / fPrice) * 10000).toFixed(1);
                            }
                            return "-";
                        }).reverse();"""
js = js.replace(data_map_old, data_map_new)

table_old = """                        let histTableHtml = `<table style="width: 100%; margin-top: 10px; border-collapse: collapse; font-size: 0.85em; text-align: center;">
                            <thead style="background: #333;"><tr>`;
                        expiries.forEach(e => histTableHtml += `<th style="padding: 4px; color: #aaa;">${e}</th>`);
                        histTableHtml += `</tr></thead><tbody><tr>`;
                        values.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: #ff9800;">${v}%</td>`);
                        histTableHtml += `</tr><tr>`;
                        spreads.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: ${v >= 0 ? '#60a5fa' : '#ff4d4d'};">${v}</td>`);
                        histTableHtml += `</tr></tbody></table>`;"""
table_new = """                        let histTableHtml = `<table style="width: 100%; margin-top: 10px; border-collapse: collapse; font-size: 0.85em; text-align: center;">
                            <thead style="background: #333;"><tr>`;
                        expiries.forEach(e => histTableHtml += `<th style="padding: 4px; color: #aaa;">${e}<br><span style="font-size:9px; color:#aaa;">Roll% | Spread | BPS</span></th>`);
                        histTableHtml += `</tr></thead><tbody><tr>`;
                        values.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: #ff9800;">${v !== null && v !== undefined ? v + '%' : '-'}</td>`);
                        histTableHtml += `</tr><tr>`;
                        spreads.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: ${v >= 0 ? '#60a5fa' : '#ff4d4d'};">${v}</td>`);
                        histTableHtml += `</tr><tr>`;
                        bpsValues.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: #ffb74d;">${v}</td>`);
                        histTableHtml += `</tr></tbody></table>`;"""
js = js.replace(table_old, table_new)

with open("backend/ui/static/js/rolloverTool.js", "w") as f:
    f.write(js)
