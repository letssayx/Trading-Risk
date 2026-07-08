// Logic for Arb Fund Marketwatch on the Derivatives page
async function loadDerivArbFundData() {
    try {
        // Fetch data targeting Arbitrage funds specifically using scheme keywords or standard ALL endpoint
        // Here we hit the same backend endpoint. We use ALL, ALL to fetch the mock data injected earlier
        // but typically you would filter for Arbitrage schemes. We use 'latest' date.
        const res = await fetch(`/api/v1/mutual-funds/hybrid?fund_house=ALL&scheme_name=ALL&date=latest`);
        const result = await res.json();
        const data = result.data || [];
        const reportDate = result.report_date || '-';

        const dateLabel = document.getElementById('deriv-arb-date-label');
        if (dateLabel) dateLabel.innerText = reportDate;

        const thead = document.getElementById('deriv-arb-thead');
        const tbody = document.getElementById('deriv-arb-tbody');
        const showPct = document.getElementById('deriv-arb-pct-toggle').checked;

        if (data.length === 0) {
            thead.innerHTML = '';
            tbody.innerHTML = `<tr><td style="text-align:center;">No data found</td></tr>`;
            return;
        }

        // Extract all unique fund names from the data payload
        const allFunds = new Set();
        data.forEach(row => {
            if (row.funds) {
                Object.keys(row.funds).forEach(f => {
                    // Filter specifically for Arbitrage funds for this specific tab logic
                    if (f.toLowerCase().includes('arbitrage')) {
                        allFunds.add(f);
                    }
                });
            }
        });
        const fundNames = Array.from(allFunds).sort();

        // Build Header dynamically
        let headerHtml = '<tr><th style="background: #252526; position: sticky; top: 0; z-index: 10; color: #cccccc; border-bottom: 2px solid #007acc;">Symbol</th><th style="background: #252526; position: sticky; top: 0; z-index: 10; color: #cccccc; border-bottom: 2px solid #007acc;">EQ Price</th><th style="background: #252526; position: sticky; top: 0; z-index: 10; color: #cccccc; border-bottom: 2px solid #007acc;">Future Price</th><th style="background: #252526; position: sticky; top: 0; z-index: 10; color: #cccccc; border-bottom: 2px solid #007acc;">Total Futures OI</th><th style="background: #252526; position: sticky; top: 0; z-index: 10; color: #cccccc; border-bottom: 2px solid #007acc;">Rollover %</th>';
        fundNames.forEach(fn => {
            headerHtml += `<th style="background: #252526; position: sticky; top: 0; z-index: 10; color: #cccccc; border-bottom: 2px solid #007acc;">${fn} (Qty)</th>`;
            if (showPct) headerHtml += `<th style="background: #252526; position: sticky; top: 0; z-index: 10; color: #cccccc; border-bottom: 2px solid #007acc;">${fn} (%)</th>`;
        });
        headerHtml += '</tr>';
        thead.innerHTML = headerHtml;

        // Build Body dynamically
        tbody.innerHTML = '';
        data.forEach(row => {
            let tr = `<tr>
                <td>${row.Symbol || '-'}</td>
                <td>${row.EQ_Price?.toFixed(2) || '-'}</td>
                <td>${row.Future_Price?.toFixed(2) || '-'}</td>
                <td>${row.Total_Futures_OI?.toLocaleString() || '-'}</td>
                <td>${row.Rollover_Pct?.toFixed(2) || '-'}%</td>
            `;

            fundNames.forEach(fn => {
                const fundData = (row.funds && row.funds[fn]) ? row.funds[fn] : {};
                tr += `<td>${fundData.qty ? fundData.qty.toLocaleString() : '-'}</td>`;
                if (showPct) {
                    tr += `<td>${fundData.pct_oi ? fundData.pct_oi.toFixed(2) + '%' : '-'}</td>`;
                }
            });
            tr += '</tr>';
            tbody.innerHTML += tr;
        });

    } catch (e) {
        console.error("Error loading Arb Fund Marketwatch data:", e);
    }
}

function exportDerivArbFundXLSX() {
    const table = document.getElementById('deriv-arb-table');
    if (!table) return;

    try {
        if (typeof XLSX !== 'undefined') {
            const wb = XLSX.utils.table_to_book(table, {sheet: "Arb Fund Marketwatch"});
            XLSX.writeFile(wb, `Arb_Fund_Marketwatch_${new Date().toISOString().split('T')[0]}.xlsx`);
        } else {
            // Fallback to CSV
            exportTableToCSV(table, `Arb_Fund_Marketwatch_${new Date().toISOString().split('T')[0]}.csv`);
        }
    } catch(e) {
        console.error("Error downloading file", e);
    }
}

// Intercept tab switching to lazy-load the data if this tab is opened
document.addEventListener("DOMContentLoaded", () => {
    // Add event listener to the button if needed, but since we rely on `switchClientTab`,
    // we can attach an observer or just hook the existing window.switchClientTab

    if (typeof window.switchClientTab === 'function') {
        const _originalSwitch = window.switchClientTab;
        window.switchClientTab = function(tabName) {
            _originalSwitch(tabName);
            if (tabName === 'arb-fund') {
                loadDerivArbFundData();
            }
        };
    }
});
