
// --- DIVIDENDS DATA BANK LOGIC ---
let divRawData = [];
let divMeetingsData = [];
let currentDivTab = 'actions';
let divSortCol = 'ex_date';
let divSortAsc = false;

function sortDividends(col) {
    if (divSortCol === col) {
        divSortAsc = !divSortAsc;
    } else {
        divSortCol = col;
        divSortAsc = true;
    }

    // Update icons
    document.getElementById('sort-icon-ex_date').innerText = '';
    document.getElementById('sort-icon-symbol').innerText = '';

    document.getElementById(`sort-icon-${col}`).innerText = divSortAsc ? '▲' : '▼';

    renderDividendsData();
}

function switchDividendsTab(tabId) {
    document.querySelectorAll('[id^="div-tab-btn-"]').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`div-tab-btn-${tabId}`).classList.add('active');

    document.getElementById('div-content-actions').style.display = tabId === 'actions' ? 'flex' : 'none';

    currentDivTab = tabId;
}

async function loadDividendsData() {
    try {
        const endDate = new Date().toISOString().split('T')[0];

        const searchInput = document.getElementById('div-symbol-search');
        const symbolQuery = searchInput && searchInput.value.trim() ? `&symbol=${searchInput.value.trim().toUpperCase()}` : '';

        // Do NOT auto-clear symbol search so user can see what they filtered
        // if (searchInput) searchInput.value = '';

        document.getElementById('div-actions-table').querySelector('tbody').innerHTML = '<tr><td colspan="7" style="text-align:center;">Loading...</td></tr>';


        // Increase limit to essentially "fetch all" if no specific symbol is provided to meet "show all scrips at one shot"
        const limitQuery = symbolQuery ? '&limit=1000' : '&limit=10000';

        const foCheckbox = document.getElementById('div-fo-only-filter');
        const foQuery = foCheckbox && foCheckbox.checked ? '&fo_only=true' : '';

        // Fetch dividends
        let dbActionsRes = await fetch(`/api/data/view/list?type=dividend${limitQuery}${symbolQuery}${foQuery}`);
        let dbActions = await dbActionsRes.json();

        // Always trust the database. If it's empty, we legitimately have no data for that symbol.
        let actions = dbActions.data || [];

        // Fetch board meetings to join
        let dbMeetingsRes = await fetch(`/api/data/view/list?type=board_meeting${limitQuery}${symbolQuery}${foQuery}`);
        let dbMeetings = await dbMeetingsRes.json();

        const meetingsArray = Array.isArray(dbMeetings) ? dbMeetings : (dbMeetings.data || []);
        if (meetingsArray.length > 0) {
             divMeetingsData = meetingsArray;
             divMeetingsData.sort((a, b) => new Date(b.meeting_date || b.date) - new Date(a.meeting_date || a.date));
        } else {
             divMeetingsData = [];
        }

        // Store fetched dividend data globally
        window.divRawData = actions;

        renderDividendsData();
    } catch(err) {
        console.error("Error loading dividends data", err);
        // Ensure UI doesn't hang in "Loading..." state on failure
        document.getElementById('div-actions-table').querySelector('tbody').innerHTML = `<tr><td colspan="7" style="text-align:center; color:red;">Error loading data: ${err.message}</td></tr>`;
    }
}

function renderDividendsData() {
    const searchInput = document.getElementById('div-symbol-search');
    const searchFilter = searchInput ? searchInput.value.toUpperCase() : '';

    // Create a map of meetings by symbol sorted by date desc for quick lookup
    const meetingsBySymbol = {};
    if (divMeetingsData && divMeetingsData.length > 0) {
        divMeetingsData.forEach(m => {
            const sym = (m.symbol || '').toUpperCase();
            if (!meetingsBySymbol[sym]) meetingsBySymbol[sym] = [];
            meetingsBySymbol[sym].push(m);
        });
    }

    // Actions Table
    const tbodyActions = document.querySelector('#div-actions-table tbody');
    if (tbodyActions) {
        tbodyActions.innerHTML = '';

        const typeFilterElem = document.getElementById('div-type-filter');
        const selectedType = typeFilterElem ? typeFilterElem.value : 'All';

        let filteredActions = divRawData.filter(d => {
            const matchSymbol = !searchFilter || (d.symbol && d.symbol.toUpperCase().includes(searchFilter));

            let matchType = true;
            if (selectedType !== 'All') {
                const purpose = (d.purpose || '').toLowerCase();
                if (selectedType === 'Interim' && !purpose.includes('interim')) matchType = false;
                else if (selectedType === 'Final' && !(purpose.includes('dividend') && !purpose.includes('interim') && !purpose.includes('special'))) matchType = false;
                else if (selectedType === 'Special' && !purpose.includes('special')) matchType = false;
                else if (selectedType === 'Bonus' && !purpose.includes('bonus')) matchType = false;
                else if (selectedType === 'Split' && !(purpose.includes('split') || purpose.includes('sub-division'))) matchType = false;
            }

            return matchSymbol && matchType;
        });

        // Sorting
        filteredActions.sort((a, b) => {
            let valA, valB;
            if (divSortCol === 'ex_date') {
                valA = a.ex_date ? new Date(a.ex_date).getTime() : 0;
                valB = b.ex_date ? new Date(b.ex_date).getTime() : 0;
            } else if (divSortCol === 'symbol') {
                valA = a.symbol || '';
                valB = b.symbol || '';
            }

            if (valA < valB) return divSortAsc ? -1 : 1;
            if (valA > valB) return divSortAsc ? 1 : -1;
            return 0;
        });

        if (filteredActions.length === 0) {
            tbodyActions.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#888;">No data found matching criteria.</td></tr>';
        }

        filteredActions.forEach(d => {
            const tr = document.createElement('tr');

            let series = d.symbol || '-';

            let matchingMeetings = meetingsBySymbol[series.toUpperCase()] || [];
            let bmd = '-';
            let agm = '-';

            if (matchingMeetings.length > 0) {
                let exDateObj = d.ex_date ? new Date(d.ex_date) : null;

                matchingMeetings.sort((a,b) => {
                    let dateA = a.meeting_date ? new Date(a.meeting_date) : new Date(0);
                    let dateB = b.meeting_date ? new Date(b.meeting_date) : new Date(0);
                    return dateB - dateA;
                });

                for (let m of matchingMeetings) {
                    if (!exDateObj || (m.meeting_date && new Date(m.meeting_date) <= exDateObj)) {
                        bmd = m.meeting_date || '-';
                        if (m.purpose && m.purpose.toUpperCase().includes('AGM')) {
                            agm = m.meeting_date || '-';
                        }
                        break;
                    }
                }

                if (bmd === '-') {
                    bmd = matchingMeetings[0].meeting_date || '-';
                    if (matchingMeetings[0].purpose && matchingMeetings[0].purpose.toUpperCase().includes('AGM')) {
                        agm = matchingMeetings[0].meeting_date || '-';
                    }
                }
            }

            let fullPurpose = d.subject || d.purpose || '-';

            let faceValue = d.face_value || d.faceValue || '-';
            if (faceValue === '-' && fullPurpose.toUpperCase().includes('FACE VALUE')) {
                 let match = fullPurpose.match(/FACE VALUE[:\s]+([\d\.]+)/i);
                 if (match) faceValue = match[1];
            }

            tr.innerHTML = `
                <td>${series}</td>
                <td>${faceValue}</td>
                <td>${fullPurpose}</td>
                <td>${d.ex_date || '-'}</td>
                <td>${d.record_date || '-'}</td>
                <td>${bmd}</td>
                <td>${agm}</td>
            `;
            tbodyActions.appendChild(tr);
        });
    }

}

function downloadDividendsCSV() {
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
                if (val.search(/("|,|\n)/g) >= 0) {
                    val = `"${val}"`;
                }
            }
            return val;
        });
        csvRows.push(values.join(','));
    }

    const csvData = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const csvUrl = URL.createObjectURL(csvData);
    const hiddenElement = document.createElement('a');
    hiddenElement.href = csvUrl;
    hiddenElement.target = '_blank';
    hiddenElement.download = filename;
    hiddenElement.click();
}

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('div-symbol-search');
    if (searchInput) {
        searchInput.addEventListener('input', renderDividendsData);
    }
});
