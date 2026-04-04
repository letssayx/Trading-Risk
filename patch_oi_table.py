import re

with open('backend/ui/static/js/oiTool.js', 'r') as f:
    content = f.read()

table_func = """
    renderDerivedTable: function() {
        const tbody = document.getElementById('oi-derived-body');
        if (!tbody) return;

        let displayData = [...this.allData];
        if (this.currentSectorFilter) {
            displayData = displayData.filter(d => d.sector === this.currentSectorFilter);
        }

        displayData.sort((a, b) => {
            let valA = a[this.currentSortCol];
            let valB = b[this.currentSortCol];

            if (typeof valA === 'string') valA = valA.toUpperCase();
            if (typeof valB === 'string') valB = valB.toUpperCase();

            if (valA < valB) return this.currentSortAsc ? -1 : 1;
            if (valA > valB) return this.currentSortAsc ? 1 : -1;
            return 0;
        });

        let html = '';
        displayData.forEach(d => {
            let pColor = d.price_chg_pct >= 0 ? '#4caf50' : '#f44336';
            let oColor = d.oi_chg_pct >= 0 ? '#4caf50' : '#f44336';

            // Build historical nested table without headers
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
                </tr>
                <tr id="oi-history-${d.symbol}" class="deriv-history-row" style="display: none;">
                    <td colspan="10" style="padding: 0;">${histHtml}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    },

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

start_idx = content.find("renderDerivedTable: function() {")
if start_idx != -1:
    end_idx = content.find("analyzeSingle: async function() {", start_idx)
    content = content[:start_idx] + table_func + "\n    " + content[end_idx:]

    with open('backend/ui/static/js/oiTool.js', 'w') as f:
        f.write(content)
    print("Patched table history in oiTool.js")
else:
    print("Could not find renderDerivedTable.")
