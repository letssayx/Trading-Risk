let mfFiltersData = {};
let currentMfSubTab = 'mf-stock';

// Load Dropdowns
async function loadMfFilters() {
    try {
        const res = await fetch('/api/v1/mutual-funds/filters');
        const data = await res.json();
        mfFiltersData = data.filters || {};

        const fundSelect = document.getElementById('mf-fund-house-select');
        fundSelect.innerHTML = '<option value="ALL">ALL</option>';
        Object.keys(mfFiltersData).forEach(fund => {
            fundSelect.innerHTML += `<option value="${fund}">${fund}</option>`;
        });

        const dateSelect = document.getElementById('mf-date-select');
        if (dateSelect) {
             dateSelect.innerHTML = '<option value="latest">Latest</option>';
             if (data.dates) {
                  data.dates.forEach(d => {
                       dateSelect.innerHTML += `<option value="${d}">${d}</option>`;
                  });
             }
        }

        mfFundHouseChanged();
    } catch (e) {
        console.error("Error loading MF filters:", e);
    }
}

function mfFundHouseChanged() {
    const fund = document.getElementById('mf-fund-house-select').value;
    const schemeSelect = document.getElementById('mf-scheme-select');
    schemeSelect.innerHTML = '<option value="ALL">ALL</option>';

    if (fund !== 'ALL' && mfFiltersData[fund]) {
        mfFiltersData[fund].forEach(scheme => {
            schemeSelect.innerHTML += `<option value="${scheme}">${scheme}</option>`;
        });
    } else {
        // If ALL selected, show all schemes across all funds
        const allSchemes = new Set();
        Object.values(mfFiltersData).forEach(schemes => {
            schemes.forEach(s => allSchemes.add(s));
        });
        Array.from(allSchemes).forEach(scheme => {
             schemeSelect.innerHTML += `<option value="${scheme}">${scheme}</option>`;
        });
    }
    mfLoadData();
}

function switchMfSubTab(tabId) {
    document.querySelectorAll('.mf-sub-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.mf-sub-tab-content').forEach(c => c.style.display = 'none');

    document.querySelector(`.mf-sub-tab[data-target="${tabId}"]`).classList.add('active');
    document.getElementById(`tab-${tabId}`).style.display = 'flex';

    currentMfSubTab = tabId;

    // Toggle % checkbox visibility only on hybrid tab
    document.getElementById('mf-pct-toggle-container').style.display = (tabId === 'mf-hybrid') ? 'flex' : 'none';

    mfLoadData();
}

async function mfLoadData() {
    const fund = document.getElementById('mf-fund-house-select').value;
    const scheme = document.getElementById('mf-scheme-select').value;
    const date = document.getElementById('mf-date-select') ? document.getElementById('mf-date-select').value : 'latest';

    if (currentMfSubTab === 'mf-hybrid') {
        loadMfHybridData(fund, scheme, date);
    } else {
        let category = 'stock';
        if (currentMfSubTab === 'mf-fo') category = 'fo';
        if (currentMfSubTab === 'mf-debt') category = 'debt';
        if (currentMfSubTab === 'mf-debt-deriv') category = 'debt_derivative';

        loadMfStandardData(fund, scheme, category, date);
    }
}

async function loadMfStandardData(fund, scheme, category, date) {
    try {
        const res = await fetch(`/api/v1/mutual-funds/holdings?fund_house=${encodeURIComponent(fund)}&scheme_name=${encodeURIComponent(scheme)}&asset_category=${category}&date=${encodeURIComponent(date)}`);
        const result = await res.json();
        const data = result.data || [];

        const tbody = document.querySelector(`#mf-${category === 'debt_derivative' ? 'debt-deriv' : category}-table tbody`);
        tbody.innerHTML = '';

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;">No data found</td></tr>`;
            return;
        }

        data.forEach(row => {
            let tr = '<tr>';
            tr += `<td>${row.report_date || '-'}</td>`;
            if (category === 'stock') {
                tr += `<td>${row.fund_house || '-'}</td><td>${row.scheme_name || '-'}</td><td>${row.symbol || '-'}</td><td>${row.isin || '-'}</td><td>${row.instrument_name || '-'}</td><td>${(row.quantity || 0).toLocaleString()}</td><td>${(row.market_value || 0).toFixed(2)}</td><td>${(row.percent_to_nav || 0).toFixed(2)}%</td>`;
            } else if (category === 'fo') {
                tr += `<td>${row.fund_house || '-'}</td><td>${row.scheme_name || '-'}</td><td>${row.instrument_name || '-'}</td><td>${row.position || '-'}</td><td>${row.option_type || '-'}</td><td>${row.strike_price || '-'}</td><td>${(row.quantity || 0).toLocaleString()}</td><td>${(row.market_value || 0).toFixed(2)}</td><td>${(row.percent_to_nav || 0).toFixed(2)}%</td>`;
            } else if (category === 'debt') {
                tr += `<td>${row.fund_house || '-'}</td><td>${row.scheme_name || '-'}</td><td>${row.isin || '-'}</td><td>${row.instrument_name || '-'}</td><td>${(row.yield_pct || 0).toFixed(2)}</td><td>${(row.coupon_pct || 0).toFixed(2)}</td><td>${row.maturity_date || '-'}</td><td>${(row.quantity || 0).toLocaleString()}</td><td>${(row.market_value || 0).toFixed(2)}</td>`;
            } else if (category === 'debt_derivative') {
                tr += `<td>${row.fund_house || '-'}</td><td>${row.scheme_name || '-'}</td><td>${row.instrument_name || '-'}</td><td>${row.benchmark || '-'}</td><td>${row.position || '-'}</td><td>${(row.notional_amount || 0).toLocaleString()}</td><td>${(row.market_value || 0).toFixed(2)}</td><td>${row.maturity_date || '-'}</td>`;
            }
            tr += '</tr>';
            tbody.innerHTML += tr;
        });
    } catch (e) {
        console.error("Error loading MF data:", e);
    }
}

async function loadMfHybridData(fund, scheme, date) {
    try {
        const res = await fetch(`/api/v1/mutual-funds/hybrid?fund_house=${encodeURIComponent(fund)}&scheme_name=${encodeURIComponent(scheme)}&date=${encodeURIComponent(date)}`);
        const result = await res.json();
        const data = result.data || [];
        const reportDate = result.report_date || '-';

        const dateLabel = document.getElementById('mf-hybrid-date-label');
        if (dateLabel) dateLabel.innerText = reportDate;

        const thead = document.getElementById('mf-hybrid-thead');
        const tbody = document.getElementById('mf-hybrid-tbody');
        const showPct = document.getElementById('mf-pct-toggle').checked;

        if (data.length === 0) {
            thead.innerHTML = '';
            tbody.innerHTML = `<tr><td style="text-align:center;">No data found</td></tr>`;
            return;
        }

        // Extract all unique fund names from the data payload
        const allFunds = new Set();
        data.forEach(row => {
            if (row.funds) {
                Object.keys(row.funds).forEach(f => allFunds.add(f));
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
        console.error("Error loading MF Hybrid data:", e);
    }
}

function mfDownloadXLSX() {
    let tableId = 'mf-stock-table';
    if (currentMfSubTab === 'mf-fo') tableId = 'mf-fo-table';
    if (currentMfSubTab === 'mf-debt') tableId = 'mf-debt-table';
    if (currentMfSubTab === 'mf-debt-deriv') tableId = 'mf-debt-deriv-table';
    if (currentMfSubTab === 'mf-hybrid') tableId = 'mf-hybrid-table';

    const table = document.getElementById(tableId);
    if (!table) return;

    try {
        if (typeof XLSX !== 'undefined') {
            const wb = XLSX.utils.table_to_book(table, {sheet: "Mutual Funds"});
            XLSX.writeFile(wb, `Mutual_Fund_${currentMfSubTab}_${new Date().toISOString().split('T')[0]}.xlsx`);
        } else {
            // Fallback to CSV
            exportTableToCSV(table, `Mutual_Fund_${currentMfSubTab}_${new Date().toISOString().split('T')[0]}.csv`);
        }
    } catch(e) {
        console.error("Error downloading file", e);
    }
}

function exportTableToCSV(table, filename) {
    let csv = [];
    let rows = table.querySelectorAll("tr");

    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll("td, th");

        for (let j = 0; j < cols.length; j++)
            row.push('"' + cols[j].innerText.replace(/"/g, '""') + '"');

        csv.push(row.join(","));
    }

    let csvFile = new Blob([csv.join("\n")], {type: "text/csv"});
    let downloadLink = document.createElement("a");
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = "none";
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// Hook into the main tab switcher logic if needed, or simply initialize when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // loadMfFilters(); // Temporarily disabled to prevent backend errors for missing tables
});
