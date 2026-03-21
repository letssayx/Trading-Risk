import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Replace the downloadDividendsCSV function
old_func = """function downloadDividendsCSV() {
    let dataToExport = currentDivTab === 'actions' ? divRawData : divMeetingsData;
    let filename = currentDivTab === 'actions' ? 'dividend_history.csv' : 'board_meetings.csv';

    const searchInput = document.getElementById('div-symbol-search');
    const searchFilter = searchInput ? searchInput.value.toUpperCase() : '';

    if (searchFilter) {
        dataToExport = dataToExport.filter(d => d.symbol && d.symbol.toUpperCase().includes(searchFilter));
        filename = `${searchFilter}_${filename}`;
    }

    if (!dataToExport || dataToExport.length === 0) {
        alert("No data available to export.");
        return;
    }

    const keys = Object.keys(dataToExport[0]);
    const csvRows = [];
    csvRows.push(keys.join(','));

    for (const row of dataToExport) {
        const values = keys.map(k => {
            let val = row[k] === null || row[k] === undefined ? '' : row[k];
            if (typeof val === 'string') {
                val = val.replace(/"/g, '""');
                if (val.search(/("|,|\n)/g) >= 0) val = `"${val}"`;
            }
            return val;
        });
        csvRows.push(values.join(','));
    }

    const csvData = csvRows.join('\\n');
    const blob = new Blob([csvData], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', filename);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}"""

new_func = """function downloadDividendsCSV() {
    const table = document.getElementById('div-actions-table');
    if (!table) {
        alert("No table found to download.");
        return;
    }

    const rows = table.querySelectorAll('tbody tr');
    if (rows.length === 0 || (rows.length === 1 && rows[0].innerText.includes('No data') || rows[0].innerText.includes('Loading'))) {
        alert("No data to download.");
        return;
    }

    let csvContent = "";
    // Extract headers matching UI table exactly
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => {
        let text = th.innerText.replace(/"/g, '""').replace(/[\\n\\r▼▲]/g, '').trim();
        return '"' + text + '"';
    });
    csvContent += headers.join(",") + "\\n";

    // Extract rows from the currently filtered/sorted DOM
    rows.forEach(tr => {
        const cells = Array.from(tr.querySelectorAll('td')).map(td => {
            let text = td.innerText.replace(/"/g, '""').trim();
            // Prefix dates/numbers that might be mangled by Excel with an apostrophe or just enclose in quotes
            return '"' + text + '"';
        });
        csvContent += cells.join(",") + "\\n";
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);

    const today = new Date().toISOString().split('T')[0];
    const searchInput = document.getElementById('div-symbol-search');
    const symbolVal = searchInput && searchInput.value.trim() ? searchInput.value.trim().toUpperCase() : '';
    const prefix = symbolVal ? symbolVal : 'all';

    link.setAttribute("download", `${prefix}_dividendhistory_${today}.csv`);

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}"""

content = content.replace(old_func, new_func)

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
