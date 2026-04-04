import re

with open('backend/ui/static/js/oiTool.js', 'r') as f:
    content = f.read()

# Replace the HTML generation in renderAggregatedView
table_func_str = """
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

# Find the loop block
start_loop = content.find("let html = '';\n            displayData.forEach(d => {")
if start_loop != -1:
    end_loop = content.find("tbody.innerHTML = html;", start_loop)
    if end_loop != -1:
        content = content[:start_loop] + table_func_str + "\n        " + content[end_loop + len("tbody.innerHTML = html;")]

        if "toggleHistory: function(" not in content:
            end_agg = content.find("renderDerivedPanels: function(universe) {")
            if end_agg != -1:
                content = content[:end_agg] + toggle_history + "\n    " + content[end_agg:]

        with open('backend/ui/static/js/oiTool.js', 'w') as f:
            f.write(content)
        print("Patched OI Tool loop.")
    else:
        print("Could not find end of loop")
else:
    print("Could not find start of loop.")
