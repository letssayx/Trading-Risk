import re

with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
    js_content = f.read()

load_fii_func = """async function loadFiiMoneyContractHistory() {
    const histDays = document.getElementById('market-activity-fii-hist-days')?.value || '30';
    try {
        const res = await fetch(`/api/market-activity/participant-oi?days=${histDays}`);
        const data = await res.json();

        const moneyRes = await fetch(`/api/market-activity/fii-stats-money?days=${histDays}`);
        const moneyData = await moneyRes.json();

        renderFIIMoneyContractHistory(data, moneyData);
    } catch(e) {
        console.error("Error loading FII Money Contract History", e);
    }
}
window.loadFiiMoneyContractHistory = loadFiiMoneyContractHistory;

window.toggleFiiHistory = function(blockId) {
    const rows = document.querySelectorAll(`tr.${blockId}`);
    if (rows.length === 0) return;
    const isHidden = rows[0].style.display === 'none';

    rows.forEach(row => {
        row.style.display = isHidden ? '' : 'none';
    });

    const icon = document.getElementById('icon-' + blockId);
    if (icon) {
        icon.className = isHidden ? 'fas fa-chevron-down' : 'fas fa-chevron-right';
    }
};

window.historicalChartInstances = window.historicalChartInstances || {};"""

js_content = js_content.replace("window.historicalChartInstances = window.historicalChartInstances || {};", load_fii_func)

js_content = js_content.replace("""            // Fetch Money Stats for the new FII history table
            const moneyRes = await fetch(`/api/market-activity/fii-stats-money?days=${histDays}`);
            const moneyData = await moneyRes.json();

            // Render Historical Net Pos Charts
            renderParticipantHistorical(data);

            // Render new FII Money & Contract History Table
            renderFIIMoneyContractHistory(data, moneyData);""", """            // Render Historical Net Pos Charts
            renderParticipantHistorical(data);

            // Trigger FII History Load independently
            if(typeof loadFiiMoneyContractHistory === 'function') loadFiiMoneyContractHistory();""")

new_render_fii_func = """function renderFIIMoneyContractHistory(contractData, moneyData) {
    const dates = contractData.dates || [];
    const tbody = document.getElementById('fii-money-contract-history-body');
    if (!tbody) return;

    if (dates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#888;">No historical data available.</td></tr>';
        return;
    }

    // Clean up old dynamically created tbodies if user reloads
    document.querySelectorAll('#fii-money-contract-history-table tbody').forEach(tb => {
        if (tb.id !== 'fii-money-contract-history-body') {
            tb.remove();
        }
    });

    tbody.innerHTML = '';

    const formatNum = (val) => {
        if (val == null || isNaN(val)) return '-';
        return parseInt(val).toLocaleString();
    };

    const getColor = (val) => {
        if (val > 0) return '#60a5fa'; // Blue for positive
        if (val < 0) return '#ff4d4d'; // Red for negative
        return '#ccc';
    };

    // Explicitly define 6 detailed bifurcation metrics to match user constraints
    const detailedMetrics = [
        { contractKey: 'fut_idx', moneyKey: 'fut_idx', label: 'Index Futures' },
        { contractKey: 'fut_stk', moneyKey: 'fut_stk', label: 'Stock Futures' },
        { contractKey: 'opt_idx_ce', moneyKey: 'opt_idx', label: 'Index Calls' },
        { contractKey: 'opt_idx_pe', moneyKey: 'opt_idx', label: 'Index Puts' },
        { contractKey: 'opt_stk_ce', moneyKey: 'opt_stk', label: 'Stock Calls' },
        { contractKey: 'opt_stk_pe', moneyKey: 'opt_stk', label: 'Stock Puts' }
    ];

    detailedMetrics.forEach(m => {
        const latestIdx = dates.length - 1;

        const getContractVal = (idx, type) => {
            if(type === 'net') return contractData[`fii_${m.contractKey}`]?.[idx] || 0;
            return contractData[`fii_${m.contractKey}_${type}`]?.[idx] || 0;
        };

        const getMoneyNetVal = (idx) => {
            return moneyData[m.moneyKey]?.[idx] || 0;
        };

        const latestL = getContractVal(latestIdx, 'long');
        const latestS = getContractVal(latestIdx, 'short');
        const latestN = getContractVal(latestIdx, 'net');
        let latestMoneyNet = getMoneyNetVal(latestIdx);

        if (m.contractKey.endsWith('_pe')) {
            latestMoneyNet = null;
        }

        const blockId = `fii-history-hist-${m.contractKey}`;
        let blockHTML = `<tbody id="tbody-fii-${m.contractKey}">`;

        blockHTML += `
            <tr style="cursor: pointer; background: #222;" onclick="toggleFiiHistory('${blockId}')">
                <td style="text-align:center;"><i class="fas fa-chevron-right" id="icon-${blockId}" style="color:#888; font-size:10px;"></i></td>
                <td style="font-weight: bold; color: #fff;">${m.label}</td>
                <td>${dates[latestIdx]}</td>
                <td style="color: ${getColor(latestMoneyNet)}; border-right: 1px solid #444; text-align: center;">${formatNum(latestMoneyNet)}</td>
                <td style="color: #60a5fa; text-align: center;">${formatNum(latestL)}</td>
                <td style="color: #ff4d4d; text-align: center;">${formatNum(latestS)}</td>
                <td style="color: ${getColor(latestN)}; border-right: 1px solid #444; text-align: center;">${formatNum(latestN)}</td>
            </tr>
        `;

        for (let i = dates.length - 2; i >= 0; i--) {
            const valL = getContractVal(i, 'long');
            const valS = getContractVal(i, 'short');
            const valN = getContractVal(i, 'net');
            let moneyNet = getMoneyNetVal(i);

            if (m.contractKey.endsWith('_pe')) {
                moneyNet = null;
            }

            blockHTML += `
                <tr class="${blockId}" style="display: none; background: #1a1a1a;">
                    <td></td>
                    <td style="color: #aaa; padding-left: 20px;">${m.label}</td>
                    <td style="color: #aaa;">${dates[i]}</td>
                    <td style="color: ${getColor(moneyNet)}; border-right: 1px solid #444; text-align: center;">${formatNum(moneyNet)}</td>
                    <td style="color: #60a5fa; text-align: center;">${formatNum(valL)}</td>
                    <td style="color: #ff4d4d; text-align: center;">${formatNum(valS)}</td>
                    <td style="color: ${getColor(valN)}; border-right: 1px solid #444; text-align: center;">${formatNum(valN)}</td>
                </tr>
            `;
        }
        blockHTML += `</tbody>`;
        document.getElementById('fii-money-contract-history-table').insertAdjacentHTML('beforeend', blockHTML);
    });
}"""

# Carefully extract and replace just the function
start_index = js_content.find("function renderFIIMoneyContractHistory(contractData, moneyData) {")
end_index = js_content.find("\nasync function loadVolatilityAnalysis() {")

if start_index != -1 and end_index != -1:
    js_content = js_content[:start_index] + new_render_fii_func + "\n" + js_content[end_index:]
else:
    print(f"Could not find exact function block. Start: {start_index}, End: {end_index}")


with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
    f.write(js_content)
