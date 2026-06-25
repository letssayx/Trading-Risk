async function loadMWPLAnalysis(forceRefresh = false) {
    const btn = document.getElementById('btn-load-mwpl');
    if (btn) btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    const tbody = document.getElementById('mwpl-analysis-body');
    if(tbody) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:20px;">Loading MWPL Analysis...</td></tr>';

    try {
        const daysRadios = document.getElementsByName('mwpl_days');
        let days = 14;
        for(let r of daysRadios) { if(r.checked) days = r.value; }

        let url = `/api/data/derivatives/mwpl_historical?days=${days}`;
        if(forceRefresh) url += '&force_refresh=true';

        const res = await fetch(url);
        if(!res.ok) throw new Error("Failed to fetch MWPL");
        const payload = await res.json();

        renderMWPLTable(payload.data);
    } catch(e) {
        console.error("MWPL error:", e);
        if(tbody) tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:red;">Error: ${e.message}</td></tr>`;
    } finally {
        if (btn) btn.innerHTML = '<i class="fas fa-sync"></i> Refresh MWPL';
    }
}

function renderMWPLTable(data) {
    const tbody = document.getElementById('mwpl-analysis-body');
    if(!tbody) return;
    tbody.innerHTML = '';

    if(!data || Object.keys(data).length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No data available</td></tr>';
        return;
    }

    // data is a dictionary: { "SYMBOL": [ {date, eq_close, fut1_close}, ... ] }
    // Flatten it to render in the table
    let allRows = [];
    for (let sym in data) {
        data[sym].forEach(r => {
            allRows.push({ symbol: sym, ...r });
        });
    }

    // Sort by date descending, then symbol
    allRows.sort((a, b) => {
        if (a.date !== b.date) return b.date.localeCompare(a.date);
        return a.symbol.localeCompare(b.symbol);
    });

    allRows.forEach(row => {
        let tr = document.createElement('tr');
        tr.innerHTML = `
            <td><b>${row.symbol}</b></td>
            <td>${row.date}</td>
            <td style="text-align:right;">${(row.eq_close || 0).toFixed(2)}</td>
            <td style="text-align:right;">${(row.fut1_close || 0).toFixed(2)}</td>
        `;
        tbody.appendChild(tr);
    });
}