import re

with open('backend/ui/static/js/specialSitTool.js', 'r') as f:
    js_code = f.read()

render_func_search = """
        html += `
            <tr style="cursor: pointer; border-bottom: 2px solid #222;" onclick="toggleSSDivHistory('${item.symbol}')">
                <td style="font-weight: bold; color: #fff;">${item.symbol}</td>
                <td>${item.lot_size || '-'}</td>
                <td>${item.spot ? item.spot.toFixed(2) : '-'}</td>
                ${futuresHTML}
                <td style="background: rgba(43, 58, 74, 0.4);">${item.last_type || '-'}</td>
                <td style="background: rgba(43, 58, 74, 0.4);">${item.last_ex_date || '-'}</td>
                <td style="background: rgba(43, 58, 74, 0.4); font-weight: bold;">${item.last_amount ? parseFloat(item.last_amount).toFixed(2) : '-'}</td>
                ${above2Cell}
                <td style="background: rgba(51, 77, 61, 0.4); color: #8fbc8f; font-weight: bold;">${item.expected_amount ? parseFloat(item.expected_amount).toFixed(2) : '-'}</td>
                <td style="background: rgba(51, 77, 61, 0.4);">${item.expected_highly_likely || '-'}</td>
                <td style="background: rgba(107, 96, 33, 0.4); color: #ffd700;">${item.expected_less_likely || '-'}</td>
                <td><button class="btn btn-secondary" style="font-size: 11px;" onclick="event.stopPropagation(); alert('AI Analyze feature coming soon')"><i class="fas fa-robot"></i> AI Analyze</button></td>
            </tr>
        `;
"""

render_func_replace = """
        let lastAmountHtml = item.last_amount ? parseFloat(item.last_amount).toFixed(2) : '-';
        let lastExDateHtml = item.last_ex_date || '-';

        // Color ex-date and amount blue if it hasn't happened yet (is in the future or today)
        if (item.history && item.history.length > 0) {
            let lastHist = item.history[0];
            if (lastHist.ex_date_obj) {
                let exDateStr = lastHist.ex_date_obj;
                // exDateStr comes from backend e.g. "2026-06-19" or ISO string
                let exDateObj = new Date(exDateStr);
                let today = new Date();
                today.setHours(0,0,0,0);
                if (exDateObj >= today) {
                    lastAmountHtml = `<span style="color: #60a5fa;">${lastAmountHtml}</span>`;
                    lastExDateHtml = `<span style="color: #60a5fa;">${lastExDateHtml}</span>`;
                }
            }
        }

        let expectedAmountHTML = item.expected_amount ? parseFloat(item.expected_amount).toFixed(2) : '-';
        if (item.expected_amount && item.last_amount) {
            let numExpected = parseFloat(item.expected_amount);
            let numLast = parseFloat(item.last_amount);
            if (numExpected > numLast) {
                expectedAmountHTML = `${expectedAmountHTML} <span style="color: #60a5fa; margin-left: 5px;">&#8593;</span>`; // Up arrow blue
            } else if (numExpected < numLast) {
                expectedAmountHTML = `${expectedAmountHTML} <span style="color: #ff4d4d; margin-left: 5px;">&#8595;</span>`; // Down arrow red
            }
        }

        html += `
            <tr style="cursor: pointer; border-bottom: 2px solid #222;" onclick="toggleSSDivHistory('${item.symbol}')">
                <td style="font-weight: bold; color: #fff;">${item.symbol}</td>
                <td>${item.lot_size || '-'}</td>
                <td>${item.spot ? item.spot.toFixed(2) : '-'}</td>
                ${futuresHTML}
                <td style="background: rgba(43, 58, 74, 0.4);">${item.last_type || '-'}</td>
                <td style="background: rgba(43, 58, 74, 0.4);">${lastExDateHtml}</td>
                <td style="background: rgba(43, 58, 74, 0.4); font-weight: bold;">${lastAmountHtml}</td>
                ${above2Cell}
                <td style="background: rgba(51, 77, 61, 0.4); color: #8fbc8f; font-weight: bold;">${expectedAmountHTML}</td>
                <td style="background: rgba(51, 77, 61, 0.4);">${item.expected_highly_likely || '-'}</td>
                <td style="background: rgba(107, 96, 33, 0.4); color: #ffd700;">${item.expected_less_likely || '-'}</td>
                <td><button class="btn btn-secondary" style="font-size: 11px;" onclick="event.stopPropagation(); alert('AI Analyze feature coming soon')"><i class="fas fa-robot"></i> AI Analyze</button></td>
            </tr>
        `;
"""

if render_func_search in js_code:
    js_code = js_code.replace(render_func_search, render_func_replace)
    with open('backend/ui/static/js/specialSitTool.js', 'w') as f:
        f.write(js_code)
    print("Patched render successfully")
else:
    print("Render block not found")
