import re

with open('backend/ui/static/js/rolloverTool.js', 'r') as f:
    content = f.read()

# Modify renderAggregatedView to clean up the nested history table
table_func = """
    renderAggregatedView: function() {
        const symbolEl = document.getElementById('rollover-symbol');
        const sectorEl = document.getElementById('rollover-sector-filter');
        const symbolFilter = symbolEl ? symbolEl.value.toUpperCase().trim() : '';
        const sectorFilter = sectorEl ? sectorEl.value : '';
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

                html += `<tr class="roll-row" onclick="RolloverTool.toggleHistory('${d.symbol}')" style="cursor: pointer; border-bottom: 1px solid #333;">
                    <td style="padding: 10px 8px; text-align: center;"><span id="roll-icon-${d.symbol}" style="font-size: 14px; color: #00bcd4; font-weight: bold;">+</span></td>
                    <td style="padding: 10px 8px;"><b>${d.symbol}</b></td>
                    <td style="padding: 10px 8px; color: #aaa;">${d.sector || ''}</td>
                    <td style="padding: 10px 8px; color: ${rollColor}; font-weight: bold;">${d.rollover_pct}%</td>
                    <td style="padding: 10px 8px; color: ${oColor};">${(d.oi_chg_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px;">${(d.price||0).toFixed(2)}</td>
                    <td style="padding: 10px 8px; color: ${pColor};">${(d.price_chg_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; color: ${costColor};">${d.rollover_cost}</td>
                    <td style="padding: 10px 8px; color: ${costColor};">${d.rollover_cost_pct}%</td>
                    <td style="padding: 10px 8px; color: #888;">${d.near_oi}</td>
                    <td style="padding: 10px 8px; color: #888;">${d.total_oi}</td>
                </tr>
                <tr id="roll-history-${d.symbol}" class="roll-history-row" style="display: none;">
                    <td colspan="11" style="padding: 0;">${histHtml}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
        }
    },

    toggleHistory: function(symbol) {
        const row = document.getElementById(`roll-history-${symbol}`);
        const icon = document.getElementById(`roll-icon-${symbol}`);
        if (row && icon) {
            if (row.style.display === 'none') {
                row.style.display = 'table-row';
                icon.textContent = '-';
            } else {
                row.style.display = 'none';
                icon.textContent = '+';
            }
        }
    },
"""

start_idx = content.find("renderAggregatedView: function() {")
if start_idx != -1:
    end_idx = content.find("analyzeSingle: async function() {", start_idx)
    content = content[:start_idx] + table_func + "\n    " + content[end_idx:]

    with open('backend/ui/static/js/rolloverTool.js', 'w') as f:
        f.write(content)
    print("Patched table history in rolloverTool.js")
else:
    print("Could not find renderAggregatedView.")
