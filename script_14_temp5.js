
        // --- Main Tab Logic ---
        const MAIN_TABS_ORDER = ['terminal', 'ai_analyze', 'derivatives', 'history', 'import', 'corporate_actions', 'dividends', 'audit', 'config'];

        function switchMainTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.main-tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.main-tab').forEach(el => el.classList.remove('active'));

            // Show target
            const target = document.getElementById(`tab-${tabName}`);
            if (target) {
                target.classList.add('active');
            } else {
                console.warn(`Tab ${tabName} not found`);
                return;
            }

            const tabBtn = document.querySelector(`.main-tab[data-target="${tabName}"]`);
            if (tabBtn) tabBtn.classList.add('active');

            // Trigger specific refreshes if needed
            if (tabName === 'terminal' && window.ChartTabs) ChartTabs.resizeAll();
            if (tabName === 'import' && window.uploader) window.uploader.open();
            if (tabName === 'audit') loadAuditHistory(); // Auto-load audit on switch
            if (tabName === 'ai_analyze') fetchSystemAccuracy();
            if (tabName === 'derivatives') {
                // Initialize first sub-tab if none selected
                if (!document.querySelector('.deriv-sub-tab.active')) {
                    switchDerivTab('matrix');
                } else if (document.querySelector('#deriv-tab-market').classList.contains('active')) {
                    if (typeof loadMarketActivity === 'function') loadMarketActivity();
                } else if (document.querySelector('#deriv-tab-matrix').classList.contains('active') && document.getElementById('mr-data-body').innerHTML.includes('No data')) {
                     // Automatically load NIFTY snapshot if empty
                     if (typeof loadTimeseriesData === 'function') loadTimeseriesData(false);
                }
            }

            // Note: corporate_actions load is handled by the wrapper function below
        }

        // --- Derivatives Sub-Tab Logic ---
        function switchDerivTab(tabName) {
            document.querySelectorAll('.deriv-sub-tab').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.deriv-sub-tab').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('#tab-derivatives .wb-tab').forEach(el => {
                el.classList.remove('active');
                el.style.borderBottomColor = 'transparent';
                el.style.color = '#888';
            });

            const target = document.getElementById(`deriv-tab-${tabName}`);
            const btn = document.getElementById(`deriv-tab-btn-${tabName}`);
            if (target && btn) {
                if (target.id === 'deriv-tab-market') {
                    target.style.display = 'flex';
                } else if (target.id === 'deriv-tab-matrix') {
                    target.style.display = 'flex';
                } else {
                    target.style.display = tabName === 'market' || tabName === 'matrix' ? 'flex' : 'block';
                }
                target.classList.add('active');
                btn.classList.add('active');
                btn.style.borderBottomColor = '#4ade80';
                btn.style.color = '#fff';

                // Trigger chart loading if Market Activity
                if (tabName === 'market' && typeof loadMarketActivity === 'function') {
                    loadMarketActivity();
                }
            }
        }

        // Initialize sub-tabs
        document.addEventListener('DOMContentLoaded', () => {
            switchDerivTab('matrix');
        });

        // --- Corporate Actions & Board Meetings UI ---
        let caCurrentTab = 'actions';
        let issueCurrentStatus = 'active';
        let caRawData = [];
        let caSortCol = 'date';
        let caSortAsc = false;


        function switchIssueStatus(status) {
            issueCurrentStatus = status;
            document.querySelectorAll('.status-tab').forEach(btn => {
                btn.style.color = '#a1a1aa';
                btn.style.borderBottomColor = 'transparent';
                if(btn.dataset.status === status) {
                    btn.style.color = '#4ade80';
                    btn.style.borderBottomColor = '#4ade80';
                }
            });
            renderCorporateActionsTable();
        }
        function filterCATable() { renderCorporateActionsTable(); }
        function switchCATab(tab) {
            caCurrentTab = tab;

            // UI Toggle
            document.getElementById('ca-tab-btn-actions').classList.toggle('active', tab === 'actions');
            document.getElementById('ca-tab-btn-announcements').classList.toggle('active', tab === 'announcements');
            document.getElementById('ca-tab-btn-meetings').classList.toggle('active', tab === 'meetings');
            document.getElementById('ca-tab-btn-rights').classList.toggle('active', tab === 'rights');
            document.getElementById('ca-tab-btn-ofs').classList.toggle('active', tab === 'ofs');
            document.getElementById('ca-tab-btn-tender').classList.toggle('active', tab === 'tender');
            document.getElementById('ca-tab-btn-circulars').classList.toggle('active', tab === 'circulars');

            // Show sub-tabs for Rights, OFS, Tender
            const issueTabs = ['rights', 'ofs', 'tender'];
            const tabsEl = document.getElementById('issue-status-tabs');
            if(issueTabs.includes(tab)) {
                if(tabsEl) tabsEl.style.display = 'flex';
                // Always reset to active on switch
                if(issueCurrentStatus !== 'active') switchIssueStatus('active');
            } else {
                if(tabsEl) tabsEl.style.display = 'none';
            }

            document.getElementById('ca-actions-filters').style.display = tab === 'actions' ? 'flex' : 'none';
            document.getElementById('ca-meetings-filters').style.display = tab === 'meetings' ? 'flex' : 'none';
            document.getElementById('ca-public-filters').style.display = tab === 'public' ? 'flex' : 'none';
            // Need a filter container for rights to prevent errors if we attempt to read it
            // but we don't have special filters for it, so nothing to show

            // Toggle table containers
            const isCirculars = tab === 'circulars';
            document.getElementById('ca-table-container').style.display = isCirculars ? 'none' : 'block';
            document.getElementById('ca-controls-wrapper').style.display = isCirculars ? 'none' : 'flex';
            document.querySelector('.history-status-bar').style.display = isCirculars ? 'none' : 'flex';
            document.getElementById('circulars-container').style.display = isCirculars ? 'block' : 'none';

            if (isCirculars) {
                loadCirculars();
                return;
            }

            // Clear current filters
            document.querySelectorAll('.ca-filter-cb').forEach(cb => cb.checked = false);
            document.getElementById('ca-search-input').value = '';

            // Reset state and load
            caRawData = [];
            if (tab === 'actions') caSortCol = 'exDate';
            else if (tab === 'announcements') caSortCol = 'dt'; // Announcement date
            else if (tab === 'meetings') caSortCol = 'date'; // Event cal date
            else caSortCol = 'recordDate'; // Public

            caSortAsc = false; // Descending by default

            loadCorporateActionsData();
        }

        async function loadCorporateActionsData() {
            // Auto-clear symbol per user request
            const searchInput = document.getElementById('ca-search-input');
            if (searchInput) searchInput.value = '';

            const tbody = document.getElementById('ca-main-body');
            const thead = document.getElementById('ca-main-head');
            const statusMsg = document.getElementById('ca-status-msg');
            const rowCount = document.getElementById('ca-row-count');

            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#888;">Loading data from NSE...</td></tr>';
            statusMsg.innerText = "Loading...";
            rowCount.innerText = "0 Rows";

            let endpoint = '/api/proxy/corporate-actions';
            if (caCurrentTab === 'announcements') endpoint = '/api/proxy/announcements';
            if (caCurrentTab === 'meetings') endpoint = '/api/proxy/event-calendar';
            if (caCurrentTab === 'rights') endpoint = '/api/proxy/rights';
            if (caCurrentTab === 'ofs') endpoint = '/api/proxy/ofs';
            if (caCurrentTab === 'tender') endpoint = '/api/proxy/tender';

            try {
                const response = await fetch(endpoint);
                if (!response.ok) throw new Error(`API Error: ${response.status}`);
                const data = await response.json();

                // Usually data is in an array or wrapped in a `data` key
                caRawData = Array.isArray(data) ? data : (data.data || []);

                // Format dates for sorting
                caRawData.forEach(item => {
                    if (item.exDate && item.exDate !== '-') item._date = new Date(item.exDate);
                    else if (item.bm_date && item.bm_date !== '-') item._date = new Date(item.bm_date);
                    else if (item.recordDate && item.recordDate !== '-') item._date = new Date(item.recordDate);
                    else item._date = new Date(0);

                    if (item.recDate && item.recDate !== '-') item._recDate = new Date(item.recDate);
                    else item._recDate = new Date(0);
                });

                renderCAHeaders();
                filterCATable();
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#f44336;">Failed to load data: ${err.message}</td></tr>`;
                statusMsg.innerText = "Error";
                rowCount.innerText = "0 Rows";
            }
        }

        function renderCAHeaders() {
            const thead = document.getElementById('ca-main-head');
            thead.innerHTML = '';

            const tr = document.createElement('tr');
            let cols = [];
            if (caCurrentTab === 'actions') {
                cols = [
                    { id: 'symbol', label: 'Symbol' },
                    { id: 'comp', label: 'Company' },
                    { id: 'subject', label: 'Purpose' },
                    { id: 'faceVal', label: 'Face Value' },
                    { id: 'exDate', label: 'Ex-Date' },
                    { id: 'recDate', label: 'Record Date' },
                    { id: 'attachment', label: 'Attachment' }
                ];
            } else if (caCurrentTab === 'announcements') {
                cols = [
                    { id: 'symbol', label: 'Symbol' },
                    { id: 'sm_name', label: 'Company' },
                    { id: 'desc', label: 'Subject' },
                    { id: 'an_dt', label: 'Date' },
                    { id: 'attchmntFile', label: 'Attachment' }
                ];
            } else if (caCurrentTab === 'meetings') {
                cols = [
                    { id: 'symbol', label: 'Symbol' },
                    { id: 'company', label: 'Company' },
                    { id: 'purpose', label: 'Purpose' },
                    { id: 'bm_desc', label: 'Details' },
                    { id: 'date', label: 'Meeting Date' },
                    { id: 'attachment', label: 'Attachment' }
                ];
            } else if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') {
                cols = [
                    { id: 'nseSymbol', label: 'Symbol' },
                    { id: 'companyName', label: 'Company' },
                    { id: 'issue_type', label: 'Type' },
                    { id: 'rightRatio', label: 'Details / Ratio' },
                    { id: 'stage', label: 'Stage' },
                    { id: 'offerPrice', label: 'Offer Price' },
                    { id: 'issueOpenDate', label: 'Open Date' },
                    { id: 'issueCloseDate', label: 'Close Date' },
                    { id: 'recordDate', label: 'Record Date' },
                    { id: 'attachment', label: 'Attachment' }
                ];
            }

            cols.forEach(c => {
                const th = document.createElement('th');
                let text = c.label;
                if (caSortCol === c.id) {
                    text += caSortAsc ? ' ▲' : ' ▼';
                    th.style.color = '#fff';
                }
                th.innerText = text;
                th.onclick = () => {
                    if (caSortCol === c.id) caSortAsc = !caSortAsc;
                    else { caSortCol = c.id; caSortAsc = true; }
                    filterCATable();
                };
                tr.appendChild(th);
            });
            thead.appendChild(tr);
        }

        // Helper function for Levenshtein distance based fuzzy matching in JS
        function levenshtein(a, b) {
            if (a.length === 0) return b.length;
            if (b.length === 0) return a.length;
            const matrix = [];
            for (let i = 0; i <= b.length; i++) matrix[i] = [i];
            for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
            for (let i = 1; i <= b.length; i++) {
                for (let j = 1; j <= a.length; j++) {
                    if (b.charAt(i - 1) === a.charAt(j - 1)) {
                        matrix[i][j] = matrix[i - 1][j - 1];
                    } else {
                        matrix[i][j] = Math.min(matrix[i - 1][j - 1] + 1, Math.min(matrix[i][j - 1] + 1, matrix[i - 1][j] + 1));
                    }
                }
            }
            return matrix[b.length][a.length];
        }

        function isFuzzyMatch(query, target) {
            if (!query) return true;
            if (!target) return false;
            // Simple subset match
            if (target.includes(query)) return true;

            // Fuzzy distance match (allow 1 typo per 4 characters)
            const threshold = Math.max(1, Math.floor(query.length / 4));

            // Check substrings
            const words = target.split(/[\s_-]+/);
            for (let w of words) {
                if (Math.abs(w.length - query.length) <= threshold) {
                    if (levenshtein(query, w) <= threshold) return true;
                }
            }
            return false;
        }

        function filterCATable() {
            if (!caRawData || caRawData.length === 0) return;

            const search = document.getElementById('ca-search-input').value.toLowerCase().trim();

            let activeFilters = [];
            let filterContainerId = '';
            if (caCurrentTab === 'actions') filterContainerId = 'ca-actions-filters';
            else if (caCurrentTab === 'meetings') filterContainerId = 'ca-meetings-filters';
            else if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') filterContainerId = 'ca-public-filters';

            if (filterContainerId) {
                activeFilters = Array.from(document.querySelectorAll(`#${filterContainerId} .ca-filter-cb:checked`)).map(cb => cb.value.toLowerCase());
            }


            let filtered = caRawData.filter(item => {
                // Search Match (Fuzzy)
                const sym = (item.symbol || item.bm_symbol || item.nseSymbol || '').toLowerCase();
                const comp = (item.comp || item.sm_name || item.companyName || item.company || '').toLowerCase();

                if (search && !isFuzzyMatch(search, sym) && !isFuzzyMatch(search, comp)) return false;

                // Status Filter for Rights, OFS, Tender
                if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') {
                    const status = (item.status || item.stage || '').toLowerCase();
                    if (issueCurrentStatus && issueCurrentStatus !== 'all' && status !== issueCurrentStatus.toLowerCase()) {
                        return false;
                    }
                }


                // Advanced Filters
                if (activeFilters.length > 0) {
                    if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') {
                        const issueType = (item.issue_type || '').toLowerCase();
                        let match = false;
                        for (const f of activeFilters) {
                            if (issueType === f) { match = true; break; }
                        }
                        if (!match) return false;
                    } else if (caCurrentTab === 'actions' || caCurrentTab === 'meetings') {
                        const purpose = (item.subject || item.bm_purpose || item.bm_desc || '').toLowerCase();
                        let match = false;
                        for (const f of activeFilters) {
                            if (purpose.includes(f)) { match = true; break; }
                            // Special handling for AGM/EGM
                            if (f === 'agm' && (purpose.includes('annual general meeting') || purpose.includes('extra ordinary general meeting'))) {
                                match = true; break;
                            }
                        }
                        if (!match) return false;
                    }
                }

                return true;
            });

            // Sort
            filtered.sort((a, b) => {
                let valA = a[caSortCol] || '';
                let valB = b[caSortCol] || '';

                // Use the parsed date object if sorting by a date column
                const parseDateStr = (dateStr) => {
                    if (!dateStr || dateStr === '-') return new Date(0);
                    const parts = dateStr.split('-');
                    if (parts.length === 3) {
                        const monthMap = { 'Jan':0, 'Feb':1, 'Mar':2, 'Apr':3, 'May':4, 'Jun':5, 'Jul':6, 'Aug':7, 'Sep':8, 'Oct':9, 'Nov':10, 'Dec':11 };
                        let mIndex = monthMap[parts[1].charAt(0).toUpperCase() + parts[1].slice(1).toLowerCase()];
                        if (mIndex !== undefined) return new Date(parts[2], mIndex, parseInt(parts[0], 10));
                    }
                    return new Date(0);
                };

                if (caSortCol === 'exDate' || caSortCol === 'bm_date' || caSortCol === 'recordDate' || caSortCol === 'issueOpenDate' || caSortCol === 'issueCloseDate' || caSortCol === 'dateOfBrdResIssueApproving') {
                    // Rights dates aren't fully pre-parsed in loadCorporateActionsData so parse on the fly or use existing _date
                    valA = a._date ? a._date.getTime() : parseDateStr(a[caSortCol]).getTime();
                    valB = b._date ? b._date.getTime() : parseDateStr(b[caSortCol]).getTime();
                } else if (caSortCol === 'recDate') {
                    valA = a._recDate ? a._recDate.getTime() : 0;
                    valB = b._recDate ? b._recDate.getTime() : 0;
                }

                if (valA < valB) return caSortAsc ? -1 : 1;
                if (valA > valB) return caSortAsc ? 1 : -1;
                return 0;
            });

            renderCATableData(filtered);
        }

        function renderCATableData(data) {
            const tbody = document.getElementById('ca-main-body');
            tbody.innerHTML = '';

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#888;">No data found matching criteria.</td></tr>';
                document.getElementById('ca-status-msg').innerText = "Ready";
                document.getElementById('ca-row-count').innerText = "0 Rows";
                return;
            }

            data.forEach(item => {
                const tr = document.createElement('tr');

                // Highlighting logic
                let rowColor = '';
                const purpose = (item.subject || item.bm_purpose || item.bm_desc || '').toLowerCase();
                if (purpose.includes('dividend')) rowColor = 'rgba(76, 175, 80, 0.15)'; // Soft green
                else if (purpose.includes('bonus') || purpose.includes('split')) rowColor = 'rgba(0, 188, 212, 0.15)'; // Soft cyan
                else if (purpose.includes('financial results')) rowColor = 'rgba(255, 152, 0, 0.15)'; // Soft orange

                if (rowColor) tr.style.backgroundColor = rowColor;

                const findLink = (obj) => {
                    let possibleKeys = ['attchmntFile', 'circFilelink', 'attachment', 'link', 'xmlFileName'];
                    for (let k of possibleKeys) {
                        if (obj[k]) return obj[k];
                    }
                    return null;
                };

                const linkVal = findLink(item);
                const linkUrl = linkVal ? (linkVal.startsWith('http') ? linkVal : `https://www.nseindia.com${linkVal}`) : '#';
                const linkHtml = linkVal ? `<a href="${linkUrl}" target="_blank" style="color: #4ade80; text-decoration: underline;">View PDF</a>` : '-';

                if (caCurrentTab === 'actions') {
                    tr.innerHTML = `
                        <td><strong>${item.symbol || '-'}</strong></td>
                        <td style="white-space:normal; max-width:200px;">${item.comp || '-'}</td>
                        <td style="white-space:normal; max-width:300px;">${item.subject || '-'}</td>
                        <td>${item.faceVal !== undefined && item.faceVal !== null ? item.faceVal : '-'}</td>
                        <td>${item.exDate || '-'}</td>
                        <td>${item.recDate || '-'}</td>
                        <td>${linkHtml}</td>
                    `;
                } else if (caCurrentTab === 'announcements') {
                    // Format announcement date
                    let formattedDate = '-';
                    if (item.an_dt) {
                        try {
                            // "an_dt" is often "2024-11-20 17:34:00"
                            const dateObj = new Date(item.an_dt.replace(' ', 'T'));
                            formattedDate = isNaN(dateObj.getTime()) ? item.an_dt.split(' ')[0] : dateObj.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
                        } catch(e) {
                            formattedDate = item.an_dt.split(' ')[0] || item.an_dt;
                        }
                    } else if (item.dt) {
                        formattedDate = item.dt;
                    }

                    tr.innerHTML = `
                        <td><strong>${item.symbol || '-'}</strong></td>
                        <td style="white-space:normal; max-width:200px;">${item.sm_name || '-'}</td>
                        <td style="white-space:normal; max-width:400px;">${item.desc || '-'}</td>
                        <td>${formattedDate}</td>
                        <td>${linkHtml}</td>
                    `;
                } else if (caCurrentTab === 'meetings') {
                     tr.innerHTML = `
                        <td><strong>${item.symbol || item.bm_symbol || '-'}</strong></td>
                        <td style="white-space:normal; max-width:200px;">${item.company || item.sm_name || '-'}</td>
                        <td style="white-space:normal; max-width:150px;">${item.purpose || item.bm_purpose || '-'}</td>
                        <td style="white-space:normal; max-width:300px;">${item.bm_desc || '-'}</td>
                        <td>${item.date || item.bm_date || '-'}</td>
                        <td>${linkHtml}</td>
                    `;
                } else if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') {
                    // Rights, OFS, Tender
                    let typeBadge = '';
                    if (item.issue_type === 'ofs') typeBadge = '<span class="badge" style="background:#2196F3; padding:2px 6px; border-radius:3px; color:white; font-size:11px;">OFS</span>';
                    else if (item.issue_type === 'tender') typeBadge = '<span class="badge" style="background:#FF9800; padding:2px 6px; border-radius:3px; color:white; font-size:11px;">Tender</span>';
                    else if (item.issue_type === 'rights') typeBadge = '<span class="badge" style="background:#4CAF50; padding:2px 6px; border-radius:3px; color:white; font-size:11px;">Rights</span>';
                    else typeBadge = item.issue_type || '-';

                     tr.innerHTML = `
                        <td><strong>${item.nseSymbol || '-'}</strong></td>
                        <td style="white-space:normal; max-width:200px;">${item.companyName || '-'}</td>
                        <td>${typeBadge}</td>
                        <td style="white-space:normal; max-width:200px;">${item.rightRatio || item.purpose || item.details || '-'}</td>
                        <td>${item.stage || item.status || '-'}</td>
                        <td>${item.offerPrice || item.price || '-'}</td>
                        <td>${item.issueOpenDate || '-'}</td>
                        <td>${item.issueCloseDate || '-'}</td>
                        <td>${item.recordDate || '-'}</td>
                        <td>${linkHtml}</td>
                    `;
                }
                tbody.appendChild(tr);
            });

            // Re-render headers to update sort arrows
            renderCAHeaders();

            document.getElementById('ca-status-msg').innerText = "Loaded successfully";
            document.getElementById('ca-row-count').innerText = `${data.length} Rows`;
        }

        function exportCATableCSV() {
            const thead = document.getElementById('ca-main-head');
            const tbody = document.getElementById('ca-main-body');

            if (tbody.rows.length === 0 || tbody.innerText.includes('Loading') || tbody.innerText.includes('No data')) {
                alert("No data to export.");
                return;
            }

            let csv = [];
            const headers = Array.from(thead.querySelectorAll('th')).map(th => `"${th.innerText.replace(/[▲▼]/g, '').trim()}"`);
            csv.push(headers.join(","));

            Array.from(tbody.querySelectorAll('tr')).forEach(tr => {
                const row = Array.from(tr.querySelectorAll('td')).map(td => `"${td.innerText.replace(/"/g, '""')}"`);
                csv.push(row.join(","));
            });

            const blob = new Blob([csv.join("\n")], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.setAttribute('hidden', '');
            a.setAttribute('href', url);
            let filename = 'Corporate_Actions';
            if (caCurrentTab === 'meetings') filename = 'Board_Meetings';
            else if (caCurrentTab === 'announcements') filename = 'Announcements';
            else if (caCurrentTab === 'rights') filename = 'Rights_Issues';
            else if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') filename = caCurrentTab.charAt(0).toUpperCase() + caCurrentTab.slice(1);

            a.setAttribute('download', `NSE_${filename}_${new Date().toISOString().slice(0,10)}.csv`);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }

        // Trigger load Corporate Actions when switchMainTab is called (override existing hook)
        const _originalSwitchMainTab = switchMainTab;
        switchMainTab = function(tabName) {
            _originalSwitchMainTab(tabName);
            if (tabName === 'corporate_actions' && caRawData.length === 0) {
                // Initial load
                switchCATab('actions');
            }
            if (tabName === 'dividends' && window.divRawData && window.divRawData.length === 0) {
                if (typeof loadDividendsData === 'function') loadDividendsData();
            }
        };

        // --- Proxy Scrapers ---
        async function loadRights() {
            document.getElementById('rights-container').innerHTML = '<p>Loading Rights data from NSE...</p>';
            try {
                const response = await fetch('/api/proxy/rights');
                const data = await response.json();

                // NSE typically returns data inside an array or inside {data: []}
                const items = Array.isArray(data) ? data : (data.data || []);
                document.getElementById('rights-container').innerHTML = renderGenericProxyTable(items);
            } catch(e) {
                document.getElementById('rights-container').innerHTML = `<p style="color:red;">Error loading rights: ${e.message}</p>`;
            }
        }

        async function loadCirculars() {
            const container = document.getElementById('circulars-container');
            container.innerHTML = '<p>Loading Circulars data from DB/NSE...</p>';
            try {
                const response = await fetch('/api/proxy/circulars');
                const data = await response.json();
                const items = Array.isArray(data) ? data : (data.data || []);

                if (items.length === 0) {
                    container.innerHTML = "<p>No circulars found.</p>";
                    return;
                }

                let html = `
                <div class="table-wrapper" style="max-height: 600px; overflow-y: auto; border: 1px solid #333; border-radius: 4px;">
                    <table class="data-table" style="width: 100%;">
                        <thead style="position: sticky; top: 0; background: #222; z-index: 10;">
                            <tr>
                                <th style="padding: 8px;">Date</th>
                                <th style="padding: 8px;">Circular No.</th>
                                <th style="padding: 8px;">Department</th>
                                <th style="padding: 8px;">Subject</th>
                                <th style="padding: 8px;">Link</th>
                            </tr>
                        </thead>
                        <tbody>`;

                items.forEach(item => {
                    const linkUrl = item.circFile ? (item.circFile.startsWith('http') ? item.circFile : `https://www.nseindia.com${item.circFile}`) : '#';
                    const linkHtml = item.circFile ? `<a href="${linkUrl}" target="_blank" style="color: #4ade80; text-decoration: underline;">View PDF</a>` : '-';
                    html += `
                            <tr>
                                <td style="padding: 8px; white-space: nowrap;">${item.circDate || '-'}</td>
                                <td style="padding: 8px; white-space: nowrap;">${item.circNo || '-'}</td>
                                <td style="padding: 8px; white-space: nowrap;">${item.circDepartment || '-'}</td>
                                <td style="padding: 8px; min-width: 300px;">${item.sub || item.subject || '-'}</td>
                                <td style="padding: 8px;">${linkHtml}</td>
                            </tr>`;
                });

                html += `</tbody></table></div>`;
                container.innerHTML = html;
            } catch(e) {
                container.innerHTML = `<p style="color:red;">Error loading circulars: ${e.message}</p>`;
            }
        }

        function renderGenericProxyTable(dataList) {
            if(!dataList || dataList.length === 0) return "<p>No entries found (API returned empty data or was blocked by WAF).</p>";

            // Collect keys that look interesting (not deep objects)
            const keys = Object.keys(dataList[0]).filter(k =>
                typeof dataList[0][k] !== 'object' && !k.startsWith('_')
            ).slice(0, 10); // Limit to 10 cols for sanity

            let html = `<table class="history-table"><thead><tr>`;
            keys.forEach(k => html += `<th>${k.toUpperCase().replace(/_/g, ' ')}</th>`);
            html += `</tr></thead><tbody>`;

            dataList.forEach(item => {
                html += `<tr>`;
                keys.forEach(k => {
                    let val = item[k] || '';
                    if (typeof val === 'string' && (k.toLowerCase().includes('link') || k.toLowerCase() === 'url' || val.startsWith('http'))) {
                        let linkUrl = val;
                        if(val.startsWith('/') && !val.startsWith('//')) {
                            linkUrl = 'https://www.nseindia.com' + val; // Handle relative links from NSE
                        }
                        // For display, truncate long URLs
                        let displayVal = val.length > 50 ? val.substring(0, 47) + '...' : val;
                        html += `<td><a href="${linkUrl}" target="_blank" style="color:#00bcd4; text-decoration:underline;" title="${val}">${displayVal}</a></td>`;
                    } else {
                        if(typeof val === 'string' && val.length > 100) val = val.substring(0, 97) + '...';
                        html += `<td title="${item[k]}">${val}</td>`;
                    }
                });
                html += `</tr>`;
            });
            html += `</tbody></table>`;
            return html;
        }


        // --- AI-Analyze Logic ---
        let aiWs = null;

        async function fetchSystemAccuracy() {
            try {
                const res = await fetch('/api/ai/accuracy?session_id=local_trader_01');
                if(res.ok) {
                    const data = await res.json();
                    document.getElementById('accuracy-score').innerText = `${data.accuracy}%`;
                }
            } catch(e) {
                console.warn("Could not fetch AI accuracy", e);
            }
        }

        function handleAiCmd(e) {
            const inputEl = document.getElementById('ai-cmd-input');

            // Auto-resize logic
            setTimeout(() => {
                inputEl.style.height = 'auto';
                inputEl.style.height = (inputEl.scrollHeight) + 'px';
            }, 0);

            if (e.key === 'Escape') {
                if (aiWs && aiWs.readyState === WebSocket.OPEN) {
                    aiWs.send(JSON.stringify({command: "STOP"}));
                    aiWs.close();
                    document.getElementById('ai-chat-feed').innerHTML += `
                    <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM]</div>
                        <div class="log-line text-warning">[INTERRUPT] Execution halted by user.</div>
                    </div>`;
                }
            } else if (e.key === 'Enter') {
                if (e.shiftKey) {
                    // Allow multi-line
                    return;
                }
                e.preventDefault(); // Prevent default enter behavior (newline)
                const cmd = inputEl.value.trim();
                if (cmd.toUpperCase() === 'STOP') {
                    if (aiWs && aiWs.readyState === WebSocket.OPEN) {
                        aiWs.send(JSON.stringify({command: "STOP"}));
                        aiWs.close();
                        document.getElementById('ai-chat-feed').innerHTML += `
                        <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM]</div>
                            <div class="log-line text-warning">[INTERRUPT] Execution halted by STOP command.</div>
                        </div>`;
                    }
                    inputEl.value = '';
                    inputEl.style.height = 'auto'; // Reset size
                    return;
                }
                runAiAnalysis(cmd);
                inputEl.style.height = 'auto'; // Reset size
            }
        }

        function runAiAnalysis(cmd) {
            if (!cmd) return;

            const groqKey = sessionStorage.getItem('GROQ_API_KEY');
            const openrouterKey = sessionStorage.getItem('OPENROUTER_API_KEY');
            const googleKey = sessionStorage.getItem('GOOGLE_API_KEY');

            const feedContainer = document.getElementById('ai-analysis-feed');
            const chatFeed = document.getElementById('ai-chat-feed');
            const cmdInput = document.getElementById('ai-cmd-input');

            // Show Feed
            feedContainer.style.display = 'flex';

            // Clear default team members and append initial user command
            chatFeed.innerHTML = `
                <div class="chat-message user-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                    <div style="color: #ccc; font-weight: bold; margin-bottom: 5px;">[TRADER]</div>
                    <div class="log-line">> EXEC: ${cmd}</div>
                </div>
            `;

            if (!groqKey || !openrouterKey || !googleKey) {
                chatFeed.innerHTML += `
                <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                    <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM ERROR]</div>
                    <div class="log-line text-warning">[ERROR] Missing API keys. Please set them in Config tab.</div>
                </div>`;
                cmdInput.value = '';
                return;
            }

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            aiWs = new WebSocket(`${protocol}//${window.location.host}/ws/ai-analyze`);

            aiWs.onopen = () => {
                aiWs.send(JSON.stringify({
                    command: cmd,
                    keys: { groq: groqKey, openrouter: openrouterKey, google: googleKey },
                    session_id: "local_trader_01"
                }));
                cmdInput.value = '';
                cmdInput.placeholder = "Processing... (Press ESC to stop)";
                cmdInput.readOnly = true;
            };

            let currentQuantLogicBlock = null;

            aiWs.onmessage = (event) => {
                const msg = JSON.parse(event.data);

                if (msg.type === "status") {
                    chatFeed.innerHTML += `
                        <div class="chat-message status-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <div class="log-line text-emerald" style="font-size: 0.9em;">[SYSTEM] ${msg.message}</div>
                        </div>`;
                } else if (msg.type === "jules_task") {
                    let julesOutput = `
                    <div class="chat-message jules-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <div style="color: #00bcd4; font-weight: bold; margin-bottom: 5px;">[JULES PRE-PROCESS]</div>`;

                    if (msg.reasoning) {
                        julesOutput += `
                        <details style="margin-bottom: 10px;">
                            <summary style="cursor: pointer; color: #a0a0a0; font-size: 0.9em;">[Thought Process]</summary>
                            <div style="padding: 10px; border-left: 2px solid #334155; margin-top: 5px; color: #888; background: #1a1c23;">
                                ${msg.reasoning.replace(/\n/g, '<br>')}
                            </div>
                        </details>`;
                    }
                    julesOutput += `<div class="log-line" style="color: #e0e0e0;"><strong>Final Task:</strong><br>${msg.message.replace(/\n/g, '<br>')}</div></div>`;
                    chatFeed.innerHTML += julesOutput;
                } else if (msg.type === "engine_type") {
                    chatFeed.innerHTML += `
                        <div class="chat-message status-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <div class="log-line text-muted" style="font-size: 0.9em;">>> Dispatched to Engine: ${msg.data.toUpperCase()}</div>
                        </div>`;
                } else if (msg.type === "quant_logic") {
                    if (!currentQuantLogicBlock) {
                        // Create new block for quant logic
                        const id = "quant-logic-" + Date.now();
                        chatFeed.insertAdjacentHTML('beforeend', `
                        <div class="chat-message deepseek-message" id="${id}" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <details>
                                <summary style="cursor: pointer; color: #64748b; font-weight: bold; margin-bottom: 5px;">[DEEPSEEK-R1] QUANT LOGIC</summary>
                                <div class="quant-content" style="color: #aaa; line-height: 1.5; white-space: pre-wrap; padding-left: 20px;"></div>
                            </details>
                        </div>`);
                        currentQuantLogicBlock = document.getElementById(id).querySelector('.quant-content');
                        currentQuantLogicBlock._inThink = false;
                    }

                    let token = msg.token;

                    if (token.includes("<think>")) {
                        token = token.replace("<think>", "");
                        currentQuantLogicBlock._inThink = true;

                        const detailsHtml = `<details open style="margin-bottom: 10px; margin-top: 10px;">
                            <summary style="cursor: pointer; color: #a0a0a0; font-size: 0.9em;">[Thought Process]</summary>
                            <div class="think-tag" style="padding: 10px; border-left: 2px solid #334155; margin-top: 5px; color: #888; background: #1a1c23; font-style: normal; display: block;"></div>
                        </details>`;
                        currentQuantLogicBlock.insertAdjacentHTML('beforeend', detailsHtml);
                    }

                    let isClosing = false;
                    if (token.includes("</think>")) {
                        token = token.replace("</think>", "");
                        isClosing = true;
                    }

                    if (token) {
                        if (currentQuantLogicBlock._inThink) {
                            const thinkTags = currentQuantLogicBlock.querySelectorAll('.think-tag');
                            if (thinkTags.length > 0) {
                                // Safe escape for innerHTML append inside think tag
                                let safeToken = token.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                                thinkTags[thinkTags.length - 1].innerHTML += safeToken;
                            } else {
                                // Fallback
                                currentQuantLogicBlock.insertAdjacentText('beforeend', token);
                            }
                        } else {
                            // If we use innerHTML += here, we wipe out the <details> state (like if it was closed)
                            // Better to use insertAdjacentText to just append text node safely
                            currentQuantLogicBlock.insertAdjacentText('beforeend', token);
                        }
                    }

                    if (isClosing) {
                        currentQuantLogicBlock._inThink = false;
                    }
                } else if (msg.type === "data_matrix") {
                    const d = msg.data;
                    let matrixOutput = `
                    <div class="chat-message qwen-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <div style="color: #e6a23c; font-weight: bold; margin-bottom: 5px;">[QWEN] DATA MATRIX</div>`;

                    if (d.qwen_reasoning) {
                        matrixOutput += `
                        <details style="margin-bottom: 10px;">
                            <summary style="cursor: pointer; color: #a0a0a0; font-size: 0.9em;">[Thought Process]</summary>
                            <div style="padding: 10px; border-left: 2px solid #334155; margin-top: 5px; color: #888; background: #1a1c23;">
                                ${d.qwen_reasoning.replace(/\n/g, '<br>')}
                            </div>
                        </details>`;
                    }

                    matrixOutput += `
                        <table class="ai-dense-table" style="width: 100%; border-collapse: collapse; font-size: 0.9em; border: 1px solid #333; margin-top: 10px;">
                            <thead>
                                <tr>
                                    <th style="border: 1px solid #333; padding: 8px; background: #16181d; color: #888; text-align: left;">SYMBOL</th>
                                    <th style="border: 1px solid #333; padding: 8px; background: #16181d; color: #888; text-align: left;">OPEN_INT</th>
                                    <th style="border: 1px solid #333; padding: 8px; background: #16181d; color: #888; text-align: left;">CHG_OI</th>
                                    <th style="border: 1px solid #333; padding: 8px; background: #16181d; color: #888; text-align: left;">IV</th>
                                    <th style="border: 1px solid #333; padding: 8px; background: #16181d; color: #888; text-align: left;">IMPLIED_MOVE</th>
                                </tr>
                            </thead>
                            <tbody>`;

                    let hasData = false;
                    if(d.equity && d.equity.close_price) {
                        hasData = true;
                        const fallbackLabel = d.yfinance_fallback ? ' <span style="color:#cca700; font-size: 0.8em;">(YF)</span>' : '';
                        matrixOutput += `
                            <tr>
                                <td style="border: 1px solid #333; padding: 8px;">${d.ticker} (EQ)${fallbackLabel}</td>
                                <td style="border: 1px solid #333; padding: 8px;">${(d.equity.total_traded_qty || 0).toLocaleString()} Vol</td>
                                <td style="border: 1px solid #333; padding: 8px;">-</td>
                                <td style="border: 1px solid #333; padding: 8px;">-</td>
                                <td style="border: 1px solid #333; padding: 8px;">₹${d.equity.close_price}</td>
                            </tr>
                        `;
                    }
                    if(d.futures && d.futures.close_price) {
                        hasData = true;
                        let oiColor = (d.futures.change_in_oi > 0) ? 'color: #10b981;' : 'color: #f59e0b;';
                        let oiSign = (d.futures.change_in_oi > 0) ? '+' : '';
                        matrixOutput += `
                            <tr>
                                <td style="border: 1px solid #333; padding: 8px;">${d.ticker}-FUT</td>
                                <td style="border: 1px solid #333; padding: 8px;">${(d.futures.open_interest || 0).toLocaleString()}</td>
                                <td style="border: 1px solid #333; padding: 8px; ${oiColor}">${oiSign}${(d.futures.change_in_oi || 0).toLocaleString()}</td>
                                <td style="border: 1px solid #333; padding: 8px;">-</td>
                                <td style="border: 1px solid #333; padding: 8px;">± ${d.futures.implied_move_pct || 0}%</td>
                            </tr>
                        `;
                    }
                    if(!hasData) {
                        matrixOutput += `<tr><td colspan="5" style="border: 1px solid #333; padding: 8px; text-align: center;">No specific DB or YFinance rows found for ${d.ticker}.</td></tr>`;
                    }
                    matrixOutput += `</tbody></table>`;

                    if (d.local_db_history || d.yfinance_history) {
                        matrixOutput += `<div style="margin-top: 10px; font-size: 0.85em; color: #a0a0a0;">`;
                        if (d.local_db_history && d.local_db_history.ticker) {
                            matrixOutput += `<details style="margin-bottom: 5px;">
                                <summary style="cursor: pointer; color: #4ade80;">[View Local DB Context: Volatility, P/E, Corp Actions]</summary>
                                <pre style="background: #111; padding: 10px; border-radius: 4px; overflow-x: auto; margin-top: 5px; color: #888;">${JSON.stringify(d.local_db_history, null, 2)}</pre>
                            </details>`;
                        }
                        if (d.yfinance_history && d.yfinance_history.history) {
                            matrixOutput += `<details style="margin-bottom: 5px;">
                                <summary style="cursor: pointer; color: #60a5fa;">[View YFinance Context: Recent History & News]</summary>
                                <pre style="background: #111; padding: 10px; border-radius: 4px; overflow-x: auto; margin-top: 5px; color: #888;">${JSON.stringify(d.yfinance_history, null, 2)}</pre>
                            </details>`;
                        }
                        matrixOutput += `</div>`;
                    }

                    matrixOutput += `</div>`;
                    chatFeed.innerHTML += matrixOutput;

                } else if (msg.type === "governance_log") {
                    chatFeed.innerHTML += `
                    <div class="chat-message llama-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <details>
                            <summary style="cursor: pointer; color: #b8860b; font-weight: bold; margin-bottom: 5px;">[GPT 120B] COMPLIANCE JUDGE</summary>
                            <div class="log-line text-warning" style="padding-left: 20px;">> ${msg.message}</div>
                        </details>
                    </div>`;
                } else if (msg.type === "execution") {
                    const ex = msg.data;
                    let actionColor = ex.action.toUpperCase().includes('SHORT') || ex.action.toUpperCase().includes('SELL') ? 'color: #f59e0b;' : 'color: #10b981;';
                    let rationaleHtml = "";
                    if (Array.isArray(ex.rationale)) {
                        rationaleHtml = "<ul style='margin-top: 5px; margin-bottom: 0; padding-left: 20px; color: #ccc;'>" + ex.rationale.map(r => `<li>${r}</li>`).join('') + "</ul>";
                    } else {
                        rationaleHtml = ex.rationale;
                    }

                    let execOutput = `
                    <div class="chat-message gemini-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <div style="color: #00bcd4; font-weight: bold; margin-bottom: 5px;">[GEMINI] EXECUTION</div>`;

                    if (ex.reasoning) {
                        execOutput += `
                        <details style="margin-bottom: 15px;">
                            <summary style="cursor: pointer; color: #a0a0a0; font-size: 0.9em;">[Thought Process]</summary>
                            <div style="padding: 10px; border-left: 2px solid #334155; margin-top: 5px; color: #888; background: #1a1c23;">
                                ${ex.reasoning.replace(/\n/g, '<br>')}
                            </div>
                        </details>`;
                    }

                    execOutput += `
                        <div class="exec-confidence" title="Calculated based on data completeness and alignment with reasoning." style="font-size: 0.85em; color: #888; margin-bottom: 5px;">CONF_SCORE: ${ex.confidence}% <span style="font-size: 0.8em; cursor: help;">(?)</span></div>
                        <div class="exec-directive" style="font-size: 1.3em; font-weight: bold; margin-bottom: 10px; ${actionColor}">ACTION: ${ex.action.toUpperCase()}</div>
                        <div class="exec-details" style="font-size: 0.9em; color: #ccc; line-height: 1.6; border-top: 1px dotted #333; padding-top: 10px;">
                            TARGET: ₹${ex.target} | STOP_LOSS: ₹${ex.stop_loss} | PREDICTED_OPEN: ₹${ex.predicted_price}<br><br>
                            <strong>RATIONALE:</strong><br> ${rationaleHtml}
                        </div>
                    </div>`;
                    chatFeed.innerHTML += execOutput;
                } else if (msg.type === "error") {
                    chatFeed.innerHTML += `
                    <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM ERROR]</div>
                        <div class="log-line text-warning">[ERROR] ${msg.message}</div>
                    </div>`;
                } else if (msg.type === "done") {
                    cmdInput.placeholder = "_";
                    cmdInput.readOnly = false;
                    cmdInput.focus();
                    aiWs.close();
                    currentQuantLogicBlock = null;
                }

                // Auto-scroll chat feed
                chatFeed.scrollTop = chatFeed.scrollHeight;
            };

            aiWs.onerror = () => {
                chatFeed.innerHTML += `
                <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                    <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM ERROR]</div>
                    <div class="log-line text-warning">[ERROR] WebSocket connection failed. Is backend running?</div>
                </div>`;
                cmdInput.placeholder = "_";
                cmdInput.readOnly = false;
            };

            aiWs.onclose = () => {
                 cmdInput.placeholder = "_";
                 cmdInput.readOnly = false;
                 currentQuantLogicBlock = null;
            }
        }

        // Global Shortcut Handler
        document.addEventListener('keydown', (e) => {
            // Avoid shortcuts when typing in inputs (except special keys if needed)
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            // Alt+Key for Tab Switching
            if (e.altKey && !e.ctrlKey && !e.shiftKey) {
                const key = e.key.toLowerCase();
                const map = {
                    't': 'terminal',
                    'h': 'history',
                    'i': 'import',
                    'a': 'ai_analyze',
                    'd': 'dividends',
                    'u': 'audit',
                    'c': 'config'
                };
                if (map[key]) {
                    e.preventDefault();
                    switchMainTab(map[key]);
                }
            }

            // Ctrl+PageUp/Down for Cycling Tabs (Excel-like)
            if (e.ctrlKey && (e.key === 'PageUp' || e.key === 'PageDown')) {
                e.preventDefault();
                const currentTab = document.querySelector('.main-tab.active');
                if (currentTab) {
                    const currentId = currentTab.dataset.target;
                    let idx = MAIN_TABS_ORDER.indexOf(currentId);
                    if (idx !== -1) {
                        if (e.key === 'PageDown') {
                            idx = (idx + 1) % MAIN_TABS_ORDER.length;
                        } else {
                            idx = (idx - 1 + MAIN_TABS_ORDER.length) % MAIN_TABS_ORDER.length;
                        }
                        switchMainTab(MAIN_TABS_ORDER[idx]);
                    }
                }
            }
        });

        // --- History Logic (Ported from data_viewer.html) ---
        let currentHistoryData = [];
        let currentSortColumn = null;
        let currentSortOrder = 'asc'; // 'asc' or 'desc'

        function updateHistoryControls() {
            const type = document.getElementById('data-type').value;
            const symbolGroup = document.getElementById('symbol-group');
            const instrumentGroup = document.getElementById('instrument-group');

            if (['fao_participant_oi', 'fii_stats', 'india_vix'].includes(type)) {
                symbolGroup.style.display = 'none';
                document.getElementById('symbol-input').value = '';
            } else {
                symbolGroup.style.display = 'flex';
            }

            if (type === 'bhavcopy_fo') {
                instrumentGroup.style.display = 'flex';
            } else {
                instrumentGroup.style.display = 'none';
                document.getElementById('instrument-input').value = 'ALL';
            }

            // Clear table on type change
            clearHistoryTable();
            // Reset sorting
            currentSortColumn = null;
            currentSortOrder = 'asc';
        }

        function clearHistoryTable() {
            document.getElementById('history-body').innerHTML = '';
            document.getElementById('history-head').innerHTML = '';
            document.getElementById('history-status-msg').innerText = "Ready";
            document.getElementById('history-row-count').innerText = "0 Rows";
            currentHistoryData = [];
        }

        async function loadHistoryData(sortBy = null, sortOrder = 'asc') {
            const type = document.getElementById('data-type').value;
            const symbolInput = document.getElementById('symbol-input');
            const symbol = symbolInput ? symbolInput.value.trim() : '';
            const start = document.getElementById('start-date').value;
            const end = document.getElementById('end-date').value;
            const instrument = document.getElementById('instrument-input') ? document.getElementById('instrument-input').value : 'ALL';

            // Auto-clear symbol per user request
            if (symbolInput) symbolInput.value = '';

            // Use current sort state if not explicitly passed
            if (!sortBy && currentSortColumn) {
                sortBy = currentSortColumn;
                sortOrder = currentSortOrder;
            }

            // Clear previous data immediately
            clearHistoryTable();
            document.getElementById('history-status-msg').innerText = "Loading...";

            const tbody = document.getElementById('history-body');
            tbody.innerHTML = '<tr><td colspan="100" style="text-align:center; color:#888;">Loading data...</td></tr>';

            const btn = document.querySelector('button[onclick="loadHistoryData()"]');
            if(btn) { btn.disabled = true; btn.innerText = "Loading..."; }

            try {
                let url = `/api/data/view/list?type=${type}&limit=500`; // Removed timestamp for speed, browser cache is usually fine with varying params
                if (symbol) url += `&symbol=${symbol}`;
                if (start) url += `&start_date=${start}`;
                if (end) url += `&end_date=${end}`;
                if (type === 'bhavcopy_fo' && instrument !== 'ALL') url += `&instrument=${instrument}`;

                // Add Server-Side Sorting Params
                if (sortBy) {
                    url += `&sort_by=${sortBy}&sort_order=${sortOrder}`;
                    currentSortColumn = sortBy;
                    currentSortOrder = sortOrder;
                }

                const res = await fetch(url);
                if (!res.ok) throw new Error(await res.text());
                const data = await res.json();
                currentHistoryData = data; // Store

                if (data.length > 0 && Object.keys(data[0]).length === 0) {
                    throw new Error("Received rows but with no columns. Data structure error.");
                }

                renderHistoryTable(data);
                document.getElementById('history-status-msg').innerText = `Loaded ${data.length} rows`;
                document.getElementById('history-row-count').innerText = `${data.length} Rows`;

            } catch (e) {
                console.error("Load History Error:", e);
                document.getElementById('history-status-msg').innerText = "Error: " + e.message;
                const tbody = document.getElementById('history-body');
                tbody.innerHTML = `<tr><td colspan="100" style="text-align:center; color:red;">Error loading data: ${e.message}</td></tr>`;
            } finally {
                if(btn) { btn.disabled = false; btn.innerText = "Load Data"; }
            }
        }

        function renderHistoryTable(data) {
            const tbody = document.getElementById('history-body');
            const thead = document.getElementById('history-head');
            tbody.innerHTML = '';
            thead.innerHTML = '';

            if (!data || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="100" style="text-align:center; color:#888;">No Data Found</td></tr>';
                return;
            }

            // Headers
            const keys = Object.keys(data[0]);
            const trHead = document.createElement('tr');
            keys.forEach((key, index) => {
                const th = document.createElement('th');

                // Sort Indicator
                let label = key.replace(/_/g, ' ').toUpperCase();
                if (key === currentSortColumn) {
                    label += (currentSortOrder === 'asc' ? ' ▲' : ' ▼');
                    th.style.color = '#fff'; // Highlight active sort column
                }

                th.innerText = label;
                th.onclick = () => sortHistoryTable(key); // Trigger Server-Side Sort
                trHead.appendChild(th);
            });
            thead.appendChild(trHead);

            // Rows
            data.forEach(row => {
                const tr = document.createElement('tr');
                keys.forEach(key => {
                    const td = document.createElement('td');
                    let val = row[key];
                    if (val === null || val === undefined) val = '-';
                    if (typeof val === 'number') {
                         // Smart formatting
                         if (Number.isInteger(val)) {
                             td.innerText = val.toLocaleString();
                         } else {
                             // Check for volatility columns or small numbers
                             if (key.includes('volatility') || key.includes('_vol') || key.includes('iv') || key.includes('rate')) {
                                 td.innerText = val.toFixed(4);
                             } else {
                                 td.innerText = val.toFixed(2);
                             }
                         }
                         td.style.textAlign = 'right';
                    } else {
                        td.innerText = val;
                    }
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
        }

        function sortHistoryTable(key) {
            // Toggle order if clicking same column, else default to asc
            let order = 'asc';
            if (key === currentSortColumn) {
                order = (currentSortOrder === 'asc') ? 'desc' : 'asc';
            }

            // Reload data with new sort params
            loadHistoryData(key, order);
        }

        async function exportHistoryData() {
            const btn = document.querySelector('button[onclick="exportHistoryData()"]');
            const originalText = btn.innerText;
            btn.disabled = true;
            btn.innerHTML = '⏳ Exporting...'; // Simple spinner effect

            const type = document.getElementById('data-type').value;
            const symbol = document.getElementById('symbol-input').value.trim();
            const start = document.getElementById('start-date').value;
            const end = document.getElementById('end-date').value;
            const instrument = document.getElementById('instrument-input') ? document.getElementById('instrument-input').value : 'ALL';

            let url = `/api/data/view/export?type=${type}`;
            if (symbol) url += `&symbol=${symbol}`;
            if (start) url += `&start_date=${start}`;
            if (end) url += `&end_date=${end}`;
            if (type === 'bhavcopy_fo' && instrument !== 'ALL') url += `&instrument=${instrument}`;

            try {
                const response = await fetch(url);
                if (!response.ok) throw new Error(await response.text());

                // Create Blob and Download
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                // Try to get filename from header or fallback
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = `${type}_export.csv`;
                if (contentDisposition) {
                    const match = contentDisposition.match(/filename=(.+)/);
                    if (match && match.length > 1) filename = match[1];
                }
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(downloadUrl);
            } catch (e) {
                console.error("Export Failed:", e);
                alert("Export failed: " + e.message);
            } finally {
                btn.disabled = false;
                btn.innerText = originalText;
            }
        }

        // --- Audit Logic ---
        function toggleDateInputs(checkbox) {
            const startInput = document.getElementById('start-date');
            const endInput = document.getElementById('end-date');
            if (checkbox.checked) {
                startInput.value = '';
                endInput.value = '';
                startInput.disabled = true;
                endInput.disabled = true;
            } else {
                startInput.disabled = false;
                endInput.disabled = false;
            }
        }

        async function deleteHistoryData() {
            const dt = document.getElementById('data-type').value;
            const sym = document.getElementById('symbol-input').value.trim();
            let start = document.getElementById('start-date').value;
            let end = document.getElementById('end-date').value;
            const isAllDates = document.getElementById('all-dates-check').checked;

            if (isAllDates) {
                start = '1900-01-01';
                end = '2100-12-31';
            }

            if (!start || !end) {
                alert("Please select both 'From' and 'To' dates to delete data within a range (or check 'All Dates').");
                return;
            }

            const msg = isAllDates ?
                `Are you sure you want to DELETE ALL DATA for '${dt}' across all dates? This will also delete the import logs so you can re-import later. THIS CANNOT BE UNDONE.` :
                `Are you sure you want to DELETE all data for '${dt}' from ${start} to ${end}? This will also delete the import logs so you can re-import later. THIS CANNOT BE UNDONE.`;

            if (!confirm(msg)) {
                return;
            }

            const btn = document.querySelector('.btn-danger');
            if(btn) { btn.disabled = true; btn.innerText = "Deleting..."; }

            try {
                const params = new URLSearchParams({
                    type: dt,
                    start_date: start,
                    end_date: end
                });

                const res = await fetch(`/api/data/view/range?${params.toString()}`, {
                    method: 'DELETE'
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Deletion failed");
                }
                const data = await res.json();
                alert(`Successfully deleted ${data.records_deleted} records and ${data.logs_deleted} import logs.`);
                loadHistoryData(); // Reload to show empty
            } catch (e) {
                alert(`Error: ${e.message}`);
            } finally {
                if(btn) { btn.disabled = false; btn.innerText = "Delete Data"; }
            }
        }

        async function loadAuditHistory() {
            const start = document.getElementById('audit-start').value;
            const end = document.getElementById('audit-end').value;
            const level = document.getElementById('audit-level') ? document.getElementById('audit-level').value : 'ALL';
            const tbody = document.getElementById('audit-log-body');
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">Loading...</td></tr>';

             try {
                let url = '/api/audit/history?limit=1000';
                if (start) url += `&start_date=${start}`;
                if (end) url += `&end_date=${end}`;
                if (level && level !== 'ALL') url += `&level=${level}`;
                const res = await fetch(url);
                const logs = await res.json();
                tbody.innerHTML = '';

                if(logs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#888;">No logs found for period</td></tr>';
                    return;
                }

                // Render logs in reverse chronological order (latest top if API sends latest first, usually)
                // Assuming API sends latest first. If not, reverse.
                // Log object: {timestamp, source, level, message}
                logs.forEach(log => {
                     const tr = document.createElement('tr');

                     // Style based on level
                     let color = '#d4d4d4';
                     if (log.level === 'ERROR') color = '#f48771';
                     else if (log.level === 'WARNING') color = '#cca700';

                     tr.style.color = color;

                     tr.innerHTML = `
                        <td>${log.timestamp.replace('T', ' ')}</td>
                        <td>${log.source}</td>
                        <td>${log.level}</td>
                        <td>${log.message}</td>
                     `;
                     tbody.appendChild(tr);
                });
                document.getElementById('log-count').innerText = `${logs.length} Events`;
             } catch(e) {
                 tbody.innerHTML = `<tr><td colspan="4" style="color:red;">Error loading logs: ${e.message}</td></tr>`;
             }
        }

        function downloadLogs() {
             const rows = Array.from(document.querySelectorAll('#audit-log-body tr'));
             if(rows.length === 0 || rows[0].innerText.includes('Loading')) return;

             let csv = "Timestamp,Source,Level,Message\n";
             rows.forEach(row => {
                 const cols = Array.from(row.querySelectorAll('td'));
                 if(cols.length < 4) return; // Skip message rows
                 const line = cols.map(c => `"${c.innerText.replace(/"/g, '""')}"`).join(",");
                 csv += line + "\n";
             });

             const blob = new Blob([csv], {type: "text/csv"});
             const link = document.createElement("a");
             link.href = URL.createObjectURL(blob);
             link.download = `Audit_Trail_${new Date().toISOString().slice(0,10)}.csv`;
             link.click();
        }

        // --- Global Autocomplete State ---
        let allGlobalSymbols = [];

        async function fetchAllSymbols() {
            try {
                const res = await fetch('/api/data/view/symbols/all');
                if(res.ok) {
                    const data = await res.json();
                    allGlobalSymbols = data.symbols || [];
                }
            } catch(e) {
                console.warn("Failed to load symbols for autocomplete", e);
            }
        }

        function setupAutocomplete(inputId) {
            const input = document.getElementById(inputId);
            if(!input) return;

            let dropdown = input.nextElementSibling;
            if (!dropdown || !dropdown.classList.contains('autocomplete-dropdown')) {
                dropdown = document.createElement('div');
                dropdown.className = 'autocomplete-dropdown';

                const wrapper = input.parentElement;
                if (!wrapper.classList.contains('autocomplete-wrapper')) {
                    const newWrapper = document.createElement('div');
                    newWrapper.className = 'autocomplete-wrapper';
                    input.parentNode.insertBefore(newWrapper, input);
                    newWrapper.appendChild(input);
                    newWrapper.appendChild(dropdown);
                } else {
                    wrapper.appendChild(dropdown);
                }
            }

            let currentFocus = -1;

            input.addEventListener('input', function() {
                const val = this.value.toUpperCase();
                dropdown.innerHTML = '';
                currentFocus = -1;

                if (!val) {
                    dropdown.style.display = 'none';
                    if (inputId === 'ca-search-input') {
                         if (typeof filterCATable === 'function') filterCATable();
                    } else if (inputId === 'div-symbol-search') {
                         if (typeof renderDividendsData === 'function') renderDividendsData();
                    }
                    return;
                }

                // If typing, trigger standard filters for some views
                if (inputId === 'ca-search-input') {
                     if (typeof filterCATable === 'function') filterCATable();
                } else if (inputId === 'div-symbol-search') {
                     if (typeof renderDividendsData === 'function') renderDividendsData();
                }

                const matches = [];
                for(let sym of allGlobalSymbols) {
                    if (sym.startsWith(val)) {
                        matches.push({sym: sym, dist: 0});
                    } else if (sym.includes(val)) {
                        matches.push({sym: sym, dist: 1});
                    } else if (val.length > 2) {
                        const lDist = levenshtein(val, sym);
                        if(lDist <= 2) {
                            matches.push({sym: sym, dist: lDist + 2});
                        }
                    }
                }

                matches.sort((a,b) => a.dist - b.dist);
                const topMatches = [...new Set(matches.map(m => m.sym))].slice(0, 10);

                if (topMatches.length > 0) {
                    topMatches.forEach(sym => {
                        const div = document.createElement('div');
                        div.innerText = sym;

                        // Highlight matching part
                        const matchIndex = sym.indexOf(val);
                        if (matchIndex !== -1) {
                            div.innerHTML = sym.substring(0, matchIndex) +
                                            "<strong>" + sym.substring(matchIndex, matchIndex + val.length) + "</strong>" +
                                            sym.substring(matchIndex + val.length);
                        }

                        div.addEventListener('mousedown', function(e) {
                            e.preventDefault();
                            input.value = sym;
                            dropdown.style.display = 'none';

                            // Auto trigger load button if it exists next to it
                            const loadBtn = input.parentElement.parentElement.querySelector('button');
                            if (loadBtn && (loadBtn.innerText.toLowerCase().includes('load') || loadBtn.innerText.toLowerCase().includes('refresh'))) {
                                loadBtn.click();
                            }

                            if (inputId === 'ca-search-input' && typeof filterCATable === 'function') filterCATable();
                            if (inputId === 'div-symbol-search' && typeof renderDividendsData === 'function') renderDividendsData();
                        });
                        dropdown.appendChild(div);
                    });
                    dropdown.style.display = 'block';
                } else {
                    dropdown.style.display = 'none';
                }
            });

            input.addEventListener('keydown', function(e) {
                const items = dropdown.getElementsByTagName('div');
                if (e.key === 'ArrowDown') {
                    currentFocus++;
                    addActive(items);
                    e.preventDefault();
                } else if (e.key === 'ArrowUp') {
                    currentFocus--;
                    addActive(items);
                    e.preventDefault();
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (currentFocus > -1) {
                        if (items[currentFocus]) {
                            input.value = items[currentFocus].innerText;
                            dropdown.style.display = 'none';
                        }
                    }

                    dropdown.style.display = 'none';

                    // Manual filters that trigger on input change for specific tabs
                    if (inputId === 'ca-search-input' && typeof filterCATable === 'function') filterCATable();
                    if (inputId === 'div-symbol-search' && typeof renderDividendsData === 'function') renderDividendsData();

                    // Explicit mapping for known input fields to their respective load functions
                    // This guarantees Enter will work, regardless of DOM structure
                    if (inputId === 'symbol-input' && typeof loadData === 'function') {
                        loadData();
                        return;
                    }
                    if (inputId === 'mr-symbol-input' && typeof applyMrFilter === 'function') {
                        applyMrFilter();
                        return;
                    }
                    if (inputId === 'market-activity-symbol' && typeof fetchMarketActivity === 'function') {
                        fetchMarketActivity();
                        return;
                    }
                    if (inputId === 'div-symbol-search' && typeof loadDividendsData === 'function') {
                        loadDividendsData();
                        return;
                    }
                    if (inputId === 'ca-search-input' && typeof loadCorporateActions === 'function') {
                        loadCorporateActions();
                        return;
                    }

                    // Auto trigger load button more robustly
                    // 1. Look for a button in the same container or parent container (up to 5 levels)
                    let currentEl = input;
                    let loadBtnFound = false;
                    for (let i = 0; i < 5; i++) {
                        if (!currentEl || currentEl.tagName === 'BODY') break;
                        const parent = currentEl.parentElement;
                        if (parent) {
                            const btns = Array.from(parent.querySelectorAll('button')).filter(btn =>
                                btn.innerText.toLowerCase().includes('load') ||
                                btn.innerText.toLowerCase().includes('refresh') ||
                                btn.innerText.toLowerCase().includes('get') ||
                                (btn.onclick && btn.onclick.toString().toLowerCase().includes('load'))
                            );
                            if (btns.length > 0) {
                                btns[0].click();
                                loadBtnFound = true;
                                break;
                            }
                        }
                        currentEl = parent;
                    }

                    // 2. If not found in immediate ancestry, look globally within the *closest active tab*
                    if (!loadBtnFound) {
                        const activeTab = input.closest('.main-tab-content') || document.querySelector('.main-tab-content.active');
                        if (activeTab) {
                            // Find the first Load/Refresh button inside this tab
                            const btns = Array.from(activeTab.querySelectorAll('button')).filter(btn =>
                                btn.innerText.toLowerCase().includes('load') ||
                                btn.innerText.toLowerCase().includes('refresh') ||
                                btn.innerText.toLowerCase().includes('get') ||
                                (btn.onclick && btn.onclick.toString().toLowerCase().includes('load'))
                            );
                            if (btns.length > 0) {
                                btns[0].click();
                                loadBtnFound = true;
                            }
                        }
                    }
                }
            });

            function addActive(items) {
                if (!items) return false;
                removeActive(items);
                if (currentFocus >= items.length) currentFocus = 0;
                if (currentFocus < 0) currentFocus = (items.length - 1);
                items[currentFocus].classList.add("autocomplete-active");
                items[currentFocus].scrollIntoView({ block: "nearest", behavior: "smooth" });
            }
        function removeActive(items) {
            }

            input.addEventListener('blur', () => {
                setTimeout(() => { dropdown.style.display = 'none'; }, 200);
            });
            input.addEventListener('focus', () => {
                if(input.value && dropdown.children.length > 0) {
                    dropdown.style.display = 'block';
                }
            });
        }

        // --- Init ---
        window.onload = () => {
            Layout.init();
            ChartTabs.init();
            WorkbookManager.init();
            connectLiveFeed();
            fetchAllSymbols().then(() => {
                setupAutocomplete('symbol-input');
                setupAutocomplete('ca-search-input');
                setupAutocomplete('div-symbol-search');
                setupAutocomplete('mr-symbol-input');
                setupAutocomplete('market-activity-symbol');
                setupAutocomplete('sm-input-symbol');
                setupAutocomplete('chart-add-input');
            });

            // Setup clock
            const dtEl = document.getElementById('global-datetime');
            setInterval(() => {
                if (dtEl) {
                    const now = new Date();
                    dtEl.innerText = now.toLocaleString();
                }
            }, 1000);

            // Set default dates
            const today = new Date().toISOString().split('T')[0];
            if(document.getElementById('end-date')) document.getElementById('end-date').value = today;
            if(document.getElementById('audit-end')) document.getElementById('audit-end').value = today;

            // Override Layout shortcuts or Uploader open
            if(window.uploader) {
                // We keep uploader logic for progress polling, but override open
                window.uploader.open = () => switchMainTab('import');
            }

            // Initialize Chat Input Handler
            const chatInput = document.getElementById('jules-input');
            const chatContent = document.getElementById('jules-content');
            if(chatInput) {
                chatInput.addEventListener('keypress', async (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        const msg = chatInput.value.trim();
                        if (!msg) return;
                        chatContent.innerHTML += `<div class="msg user" style="color:#00bcd4; margin-top:5px;"><strong>You:</strong> ${msg}</div>`;
                        chatInput.value = '';
                        // Mock Response for now as actual backend call wasn't fully visible in my read but I recall the structure
                        try {
                            const res = await fetch('/api/jules/chat', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({message: msg})
                            });
                            const data = await res.json();
                            chatContent.innerHTML += `<div class="msg jules" style="margin-top:5px;"><strong>Jules:</strong> ${data.response}</div>`;
                        } catch(err) {
                            chatContent.innerHTML += `<div class="msg error" style="color:red;">Error: ${err.message}</div>`;
                        }
                    }
                });
            }
        };

        function switchLeftTab(tab) {
             document.getElementById('jules-content').style.display = tab === 'jules' ? 'block' : 'none';
             document.getElementById('python-content').style.display = tab === 'python' ? 'block' : 'none';
             document.querySelectorAll('#lp-bottom .tab-btn').forEach(b => b.classList.remove('active'));
             if(tab === 'jules') document.querySelector('#lp-bottom .tab-btn:first-child').classList.add('active');
             else document.querySelector('#lp-bottom .tab-btn:last-child').classList.add('active');
        }

        let ws, logsWs;
        function connectLiveFeed() {
             const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
             ws = new WebSocket(`${protocol}//${window.location.host}/ws/live`);
             ws.onopen = () => { console.log("WS Connected"); ws.send(JSON.stringify({subscribe: ["NIFTY", "BANKNIFTY"]})); };
             ws.onmessage = (event) => {
                 const data = JSON.parse(event.data);
                 if(window.ChartTabs) ChartTabs.handleTick(data);
                 if(window.WorkbookManager) WorkbookManager.handleTick(data);
             };

             logsWs = new WebSocket(`${protocol}//${window.location.host}/ws/logs`);
             logsWs.onmessage = (event) => {
                 const msg = event.data;
                 const auditContainer = document.getElementById('audit-log-container');
                 if(auditContainer) {
                     const div = document.createElement('div');
                     div.innerText = msg;
                     div.style.borderBottom = '1px solid #333';
                     // Color coding
                     if (msg.includes("ERROR")) div.style.color = "#f48771";
                     else if (msg.includes("WARNING")) div.style.color = "#cca700";
                     else div.style.color = "#d4d4d4";

                     auditContainer.appendChild(div);
                     if(auditContainer.scrollHeight - auditContainer.scrollTop < 200) auditContainer.scrollTop = auditContainer.scrollHeight;
                 }

                 // Uvicorn logs via WebSocket
                 const terminal = document.getElementById('uvicorn-terminal');
                 if (terminal && !msg.includes("MainProcess") && !msg.includes("celery") && !msg.includes("NSE_Importer")) {
                     const div = document.createElement('div');
                     div.innerText = msg;
                     if (msg.includes("ERROR")) div.style.color = "#f48771";
                     else if (msg.includes("WARNING")) div.style.color = "#cca700";
                     else div.style.color = "#d4d4d4";
                     terminal.appendChild(div);
                     // Auto-scroll
                     if(terminal.scrollHeight - terminal.scrollTop < 300) terminal.scrollTop = terminal.scrollHeight;
                 }
             };

             // Polling for Celery logs from DB since they don't share the same WS loop
             let lastCeleryLogId = 0;
             setInterval(async () => {
                 const celeryTerminal = document.getElementById('celery-terminal');
                 if(!celeryTerminal || celeryTerminal.offsetParent === null) return; // Only poll if visible

                 // ONLY poll if an import is actually running, to prevent infinite looping and DB spam
                 if (!window.uploader || !window.uploader.isPolling) {
                     return;
                 }

                 try {
                     // We fetch the latest audit logs that are likely from celery
                     const res = await fetch(`/api/audit/history?limit=50`);
                     if(res.ok) {
                         const logs = await res.json();
                         // Sort ascending by ID or timestamp
                         logs.sort((a,b) => a.id - b.id);

                         // On first load, don't dump 200 logs, just get the last 20
                         if (lastCeleryLogId === 0 && logs.length > 0) {
                             lastCeleryLogId = logs[Math.max(0, logs.length - 20)].id - 1;
                         }

                         let newLogs = logs.filter(l => l.id > lastCeleryLogId && l.source === 'NSE_Importer');
                         if(newLogs.length > 0) {
                             lastCeleryLogId = newLogs[newLogs.length - 1].id;
                             newLogs.forEach(log => {
                                 const div = document.createElement('div');
                                 div.innerText = `[${log.timestamp.replace('T', ' ').substring(0, 19)}] ${log.level} [${log.source}] ${log.message}`;
                                 if (log.level === "ERROR" || log.level === "FAILED") div.style.color = "#f48771";
                                 else if (log.level === "WARNING") div.style.color = "#cca700";
                                 else div.style.color = "#d4d4d4";
                                 celeryTerminal.appendChild(div);
                             });
                             celeryTerminal.scrollTop = celeryTerminal.scrollHeight;
                         }
                     }
                 } catch(e) {
                     // silent fail for poller
                 }
             }, 2000);
        }
