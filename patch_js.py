import re

with open('backend/ui/static/js/specialSitTool.js', 'r') as f:
    js_code = f.read()

new_funcs = """

function clearSSDivSearch() {
    const input = document.getElementById('ss-div-search');
    if (input) {
        input.value = '';
        filterSSDividends();
    }
}

function exportSSDivCSV() {
    if (!ssDivData || ssDivData.length === 0) return;
    let csv = 'Index / Scrip,Lot size,Spot,Future 1,Future 2,Future 3,Type,Ex-date,Amount,Is above 2% (Extra-ordinary),Expected Amount,Expected Dividend highly likely,Expected Dividend Less Likely\\n';

    const filter = document.getElementById('ss-div-search').value.trim().toUpperCase();

    ssDivData.forEach(item => {
        if (filter && !item.symbol.includes(filter)) return;
        let row = [];
        row.push(item.symbol || '-');
        row.push(item.lot_size || '-');
        row.push(item.spot ? item.spot.toFixed(2) : '-');
        row.push(item.futures && item.futures[0] ? item.futures[0].toFixed(2) : '-');
        row.push(item.futures && item.futures[1] ? item.futures[1].toFixed(2) : '-');
        row.push(item.futures && item.futures[2] ? item.futures[2].toFixed(2) : '-');
        row.push(item.last_type || '-');
        row.push(item.last_ex_date || '-');
        row.push(item.last_amount || '-');
        row.push(item.is_above_2_percent ? 'Yes' : 'No');
        row.push(item.expected_amount || '-');
        row.push(item.expected_highly_likely || '-');
        row.push(item.expected_less_likely || '-');

        csv += '"' + row.join('","') + '"\\n';
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', 'dividend_arbitrage.csv');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function exportSSDivPDF() {
    const table = document.getElementById('ss-div-table');
    if (!table) return;

    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write('<html><head><title>Dividend Arbitrage Scenario</title>');
    printWindow.document.write('<style>');
    printWindow.document.write('table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 12px; }');
    printWindow.document.write('th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }');
    printWindow.document.write('th { background-color: #f2f2f2; }');
    printWindow.document.write('.mwpl-blue { color: #3176B8; font-weight: bold; }');
    printWindow.document.write('.mwpl-red { color: #ff4d4d; font-weight: bold; }');
    printWindow.document.write('</style>');
    printWindow.document.write('</head><body>');
    printWindow.document.write('<h2>Dividend Arbitrage Scenario</h2>');

    // Create a clone of the table but remove the 'Action' column and hidden history rows
    const cloneTable = table.cloneNode(true);

    // Remove history rows
    const historyRows = cloneTable.querySelectorAll('tr[id^="ss-div-hist-"]');
    historyRows.forEach(r => r.parentNode.removeChild(r));

    // Remove last column (Action) from header and body
    const trs = cloneTable.querySelectorAll('tr');
    trs.forEach(tr => {
        if(tr.children.length > 0) {
            tr.removeChild(tr.lastElementChild);
        }
    });

    printWindow.document.write(cloneTable.outerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

"""

js_code = js_code.replace("function toggleSSDivHistory(symbol) {", new_funcs + "function toggleSSDivHistory(symbol) {")

with open('backend/ui/static/js/specialSitTool.js', 'w') as f:
    f.write(js_code)
