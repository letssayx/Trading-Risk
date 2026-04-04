import re

with open('backend/ui/static/js/oiTool.js', 'r') as f:
    content = f.read()

# Let's search for "renderAggregatedView" and modify the table rendering part
table_func_str = """
        // Render Table
        const tbody = document.getElementById('oi-derived-body');
        if (tbody) {
            let html = '';
            displayData.forEach(d => {
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

                html += `<tr class="deriv-row" onclick="OiTool.toggleHistory('${d.symbol}')" style="cursor: pointer; border-bottom: 1px solid #333;">
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
                </tr>
                <tr id="oi-history-${d.symbol}" class="deriv-history-row" style="display: none;">
                    <td colspan="10" style="padding: 0;">${histHtml}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
        }
"""

toggle_history = """
    toggleHistory: function(symbol) {
        const row = document.getElementById(`oi-history-${symbol}`);
        const icon = document.getElementById(`oi-icon-${symbol}`);
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

import re
# Find the render Table block in renderAggregatedView
table_block_start = content.find("// Render Table")
if table_block_start != -1:
    table_block_end = content.find("this.renderDerivedPanels(baseUniverse);", table_block_start)
    if table_block_end != -1:
        content = content[:table_block_start] + table_func_str + "\n        " + content[table_block_end:]

        # Add toggleHistory if not present
        if "toggleHistory: function(" not in content:
            # find end of renderAggregatedChart
            end_chart = content.find("renderDerivedPanels: function(universe) {")
            if end_chart != -1:
                content = content[:end_chart] + toggle_history + "\n    " + content[end_chart:]

        with open('backend/ui/static/js/oiTool.js', 'w') as f:
            f.write(content)
        print("Patched OI table.")
    else:
        print("Could not find end of table block")
else:
    print("Could not find table block.")
