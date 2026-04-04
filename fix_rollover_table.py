import re

with open("backend/ui/static/js/rolloverTool.js", "r") as f:
    content = f.read()

# Replace the table headers in render
new_render_html = """
                                <thead>
                                    <tr style="position: sticky; top: 0; background: #222; z-index: 10; border-bottom: 2px solid #00bcd4;">
                                        <th style="padding: 8px; width: 30px;"></th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('symbol')">Symbol ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_pct')">Rollover % ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost')">Spread (Pts) ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost_pct')">Cost % ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('fut_close')">FUT Price ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('price_chg_pct')">Price Chg % ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('oi_chg_pct')">OI Chg % ↕</th>
                                        <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('total_oi')">Total OI ↕</th>
                                    </tr>
                                </thead>
"""

content = re.sub(r'<thead>.*?</thead>', new_render_html, content, flags=re.DOTALL)

# Add toggleHistory method
toggle_history_fn = """
    toggleHistory: function(symbol) {
        const row = document.getElementById(`roll-history-${symbol}`);
        const icon = document.getElementById(`roll-icon-${symbol}`);
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
"""

content = content.replace("filterData: function() {", toggle_history_fn + "\n    filterData: function() {")


# Update renderAggregatedView to include history
new_tbody_logic = """
        if (displayData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#888;">No F&O stocks found.</td></tr>';
        } else {
            let html = '';
            displayData.forEach(d => {
                let costColor = d.rollover_cost >= 0 ? '#4caf50' : '#f44336';
                let rollColor = d.rollover_pct >= 80 ? '#00bcd4' : '#ccc';
                let pColor = d.price_chg_pct >= 0 ? '#4caf50' : '#f44336';
                let oColor = d.oi_chg_pct >= 0 ? '#4caf50' : '#f44336';

                let histHtml = '';
                if (d.history && d.history.length > 0) {
                    histHtml = `
                        <div style="padding: 10px 40px; background: #151515; border-bottom: 1px solid #333;">
                            <table style="width: 100%; border-collapse: collapse; font-size: 0.85em; text-align: left; color: #bbb;">
                                <thead>
                                    <tr style="border-bottom: 1px solid #444;">
                                        <th style="padding: 6px 10px; font-weight: normal; color: #888;">Date</th>
                                        <th style="padding: 6px 10px; font-weight: normal; color: #888;">Rollover %</th>
                                        <th style="padding: 6px 10px; font-weight: normal; color: #888;">FUT Price</th>
                                        <th style="padding: 6px 10px; font-weight: normal; color: #888;">Price Chg %</th>
                                        <th style="padding: 6px 10px; font-weight: normal; color: #888;">Total OI</th>
                                        <th style="padding: 6px 10px; font-weight: normal; color: #888;">OI Chg %</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;
                    d.history.forEach((h, idx) => {
                        let hpColor = h.price_chg_pct >= 0 ? '#4caf50' : '#f44336';
                        let hoColor = h.oi_chg_pct >= 0 ? '#4caf50' : '#f44336';
                        let rowBg = idx % 2 === 0 ? '#1f1f1f' : '#1a1a1a';
                        histHtml += `<tr style="background: ${rowBg};">
                            <td style="padding: 6px 10px;">${h.date}</td>
                            <td style="padding: 6px 10px; color: #00bcd4;">${(h.rollover_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 10px;">${(h.price || 0).toFixed(2)}</td>
                            <td style="padding: 6px 10px; color: ${hpColor}">${(h.price_chg_pct || 0).toFixed(2)}%</td>
                            <td style="padding: 6px 10px;">${(h.oi || 0).toLocaleString()}</td>
                            <td style="padding: 6px 10px; color: ${hoColor}">${(h.oi_chg_pct || 0).toFixed(2)}%</td>
                        </tr>`;
                    });
                    histHtml += `</tbody></table></div>`;
                } else {
                    histHtml = `<div style="padding: 10px 40px; color: #888; background: #1a1a1a;">No historical data available</div>`;
                }

                html += `
                <tr class="roll-row" onclick="RolloverTool.toggleHistory('${d.symbol}')" style="cursor: pointer; border-bottom: 1px solid #333; transition: background 0.2s;" onmouseover="this.style.background='#2a2a2a'" onmouseout="this.style.background='transparent'">
                    <td style="padding: 10px 8px; text-align: center;"><span id="roll-icon-${d.symbol}" style="font-size: 14px; color: #00bcd4; font-weight: bold;">▶</span></td>
                    <td style="padding: 10px 8px;"><b>${d.symbol}</b></td>
                    <td style="padding: 10px 8px; color: ${rollColor}; font-weight: bold;">${(d.rollover_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; color: ${costColor};">${(d.rollover_cost||0).toFixed(2)}</td>
                    <td style="padding: 10px 8px; color: ${costColor};">${(d.rollover_cost_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px;">${(d.fut_close||0).toFixed(2)}</td>
                    <td style="padding: 10px 8px; color: ${pColor};">${(d.price_chg_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; color: ${oColor};">${(d.oi_chg_pct||0).toFixed(2)}%</td>
                    <td style="padding: 10px 8px; color: #ccc;">${(d.total_oi||0).toLocaleString()}</td>
                </tr>
                <tr id="roll-history-${d.symbol}" class="roll-history-row" style="display: none;">
                    <td colspan="9" style="padding: 0;">${histHtml}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
        }
"""

content = re.sub(r'if \(displayData\.length === 0\) \{.*?tbody\.innerHTML = html;\s*\}', new_tbody_logic, content, flags=re.DOTALL)

with open("backend/ui/static/js/rolloverTool.js", "w") as f:
    f.write(content)
