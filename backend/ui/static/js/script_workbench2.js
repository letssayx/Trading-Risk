        // --- Main Tab Logic ---
        const MAIN_TABS_ORDER = ['terminal', 'ai_analyze', 'derivatives', 'history', 'import', 'corporate_actions', 'audit', 'config'];

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

            // Re-render ECharts or resize them since they might have collapsed while hidden
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 10);
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
                } else if (target.id === 'deriv-tab-oi') {
                    target.style.display = 'flex';
                } else {
                    target.style.display = 'block';
                }
                target.classList.add('active');
                btn.classList.add('active');
                btn.style.borderBottomColor = '#60a5fa';
                btn.style.color = '#fff';

                // Trigger chart loading if Market Activity
                if (tabName === 'market' && typeof loadMarketActivity === 'function') {
                    loadMarketActivity();
                }

                // Trigger options charts if OI Analysis
                if (tabName === 'oi' && typeof loadOptionsAnalysis === 'function') {
                    loadOptionsAnalysis();
                }

                // Trigger Volatility Analysis
                if (tabName === 'optanalysis' && typeof loadVolatilityAnalysis === 'function') {
                    loadVolatilityAnalysis();
                }

                // Trigger Advanced Technicals
                if (tabName === 'advtech' && typeof loadDynamicChart === 'function') {
                    loadDynamicChart();
                }

                // Re-render ECharts or resize them since they might have collapsed while hidden
                setTimeout(() => {
                    window.dispatchEvent(new Event('resize'));
                }, 10);
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
                    btn.style.color = '#60a5fa';
                    btn.style.borderBottomColor = '#60a5fa';
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
            const tbody = document.getElementById('ca-main-body');
            const thead = document.getElementById('ca-main-head');
            const statusMsg = document.getElementById('ca-status-msg');
            const rowCount = document.getElementById('ca-row-count');

            tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; color:#888;">Loading data from NSE...</td></tr>';
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
                tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; color:#f44336;">Failed to load data: ${err.message}</td></tr>`;
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
                tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; color:#888;">No data found matching criteria.</td></tr>';
                document.getElementById('ca-status-msg').innerText = "Ready";
                document.getElementById('ca-row-count').innerText = "0 Rows";
                return;
            }

            data.forEach(item => {
                const tr = document.createElement('tr');

                // Highlighting logic
                let rowColor = '';
                const purpose = (item.subject || item.bm_purpose || item.bm_desc || '').toLowerCase();
                if (purpose.includes('dividend')) rowColor = 'rgba(49, 118, 184, 0.15)'; // Soft green
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
                const linkHtml = linkVal ? `<a href="${linkUrl}" target="_blank" style="color: #60a5fa; text-decoration: underline;">View PDF</a>` : '-';

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
                    else if (item.issue_type === 'rights') typeBadge = '<span class="badge" style="background:#60a5fa; padding:2px 6px; border-radius:3px; color:white; font-size:11px;">Rights</span>';
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
                    const linkHtml = item.circFile ? `<a href="${linkUrl}" target="_blank" style="color: #60a5fa; text-decoration: underline;">View PDF</a>` : '-';
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
                        html += `<td><a href="${linkUrl}" target="_blank" style="color:#60a5fa; text-decoration:underline;" title="${val}">${displayVal}</a></td>`;
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
                        <div style="color: #60a5fa; font-weight: bold; margin-bottom: 5px;">[JULES PRE-PROCESS]</div>`;

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
                        let oiColor = (d.futures.change_in_oi > 0) ? 'color: #60a5fa;' : 'color: #f59e0b;';
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
                                <summary style="cursor: pointer; color: #60a5fa;">[View Local DB Context: Volatility, P/E, Corp Actions]</summary>
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
                    let actionColor = ex.action.toUpperCase().includes('SHORT') || ex.action.toUpperCase().includes('SELL') ? 'color: #f59e0b;' : 'color: #60a5fa;';
                    let rationaleHtml = "";
                    if (Array.isArray(ex.rationale)) {
                        rationaleHtml = "<ul style='margin-top: 5px; margin-bottom: 0; padding-left: 20px; color: #ccc;'>" + ex.rationale.map(r => `<li>${r}</li>`).join('') + "</ul>";
                    } else {
                        rationaleHtml = ex.rationale;
                    }

                    let execOutput = `
                    <div class="chat-message gemini-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <div style="color: #60a5fa; font-weight: bold; margin-bottom: 5px;">[GEMINI] EXECUTION</div>`;

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
                            TARGET: ₹${ex.target} | STOP_LOSS: ₹${ex.stop_loss}<br><br>
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
            const symbol = document.getElementById('symbol-input').value.trim();
            const start = document.getElementById('start-date').value;
            const end = document.getElementById('end-date').value;
            const instrument = document.getElementById('instrument-input') ? document.getElementById('instrument-input').value : 'ALL';
            const isLatest = document.getElementById('latest-date-check').checked;

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
                // If "Latest" is checked but symbol is provided, we still want the timeseries for that symbol,
                // otherwise we just want the cross-section of all symbols for the latest date.
                // User requirement: "Latest Date check box has stopped working in Historical" -> "in the historical data section"
                // The 'latest' flag on the backend gets the max date. If we force limit=1, we only get ONE row (one symbol).
                // We should pass limit=0 (unlimited) or a high number like 5000 if we want all symbols for that latest date.
                let limit = isLatest ? 5000 : 500;
                if (symbol && isLatest) limit = 1; // if symbol is specified and latest is checked, we only need 1 row
                let url = `/api/data/view/list?type=${type}&limit=${limit}`;
                if (symbol) {
                    url += `&symbol=${symbol}`;
                }
                if (start) url += `&start_date=${start}`;
                if (end) url += `&end_date=${end}`;
                if (type === 'bhavcopy_fo' && instrument !== 'ALL') url += `&instrument=${instrument}`;
                if (isLatest) url += `&latest=true`;

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
            const isLatest = document.getElementById('latest-date-check').checked;

            let url = `/api/data/view/export?type=${type}`;
            if (symbol) url += `&symbol=${symbol}`;
            if (start) url += `&start_date=${start}`;
            if (end) url += `&end_date=${end}`;
            if (type === 'bhavcopy_fo' && instrument !== 'ALL') url += `&instrument=${instrument}`;
            if (isLatest) url += `&latest=true`;

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
                document.getElementById('latest-date-check').checked = false;
            } else {
                startInput.disabled = false;
                endInput.disabled = false;
            }
        }

        function toggleDateInputsLatest(checkbox) {
            const startInput = document.getElementById('start-date');
            const endInput = document.getElementById('end-date');
            if (checkbox.checked) {
                startInput.value = '';
                endInput.value = '';
                startInput.disabled = true;
                endInput.disabled = true;
                document.getElementById('all-dates-check').checked = false;
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

        // --- Init ---
        window.onload = () => {
            Layout.init();
            ChartTabs.init();
            WorkbookManager.init();
            connectLiveFeed();

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
                        chatContent.innerHTML += `<div class="msg user" style="color:#60a5fa; margin-top:5px;"><strong>You:</strong> ${msg}</div>`;
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
// script end
// script start
// script start
    let echartInstance = null;
    let fiiDiiChartInstance = null;
    let participantChartInstance = null;

    async function loadMarketActivity() {
        const symbol = document.getElementById('market-activity-symbol').value.toUpperCase() || 'NIFTY';

        // 1. Load FII/DII Chart (Side by side bars per user request)
        try {
            const res = await fetch('/api/market-activity/cash-flow');
            const data = await res.json();
            if (fiiDiiChartInstance) fiiDiiChartInstance.destroy();
            const ctx = document.getElementById('fiiDiiChart').getContext('2d');

            // Extract Nifty prices dynamically if returned
            const niftyData = data.nifty_close || [];

            // Add NIFTY line overlay dynamically to FII/DII Chart if NIFTY exists
            const datasets = [
                {
                    label: 'FII Net',
                    type: 'bar',
                    yAxisID: 'y',
                    data: data.fii_net,
                    backgroundColor: '#E88B1E',
                    borderColor: '#E88B1E',
                    borderWidth: 0,
                    barPercentage: 1.0,
                    categoryPercentage: 0.8,
                    datalabels: { align: 'end', anchor: 'end', color: '#ccc', font: {size: 9}, formatter: (value) => value === 0 ? '' : Math.round(value) }
                }, // Orange
                {
                    label: 'DII Net',
                    type: 'bar',
                    yAxisID: 'y',
                    data: data.dii_net,
                    backgroundColor: '#60a5fa',
                    borderColor: '#60a5fa',
                    borderWidth: 0,
                    barPercentage: 1.0,
                    categoryPercentage: 0.8,
                    datalabels: { align: 'end', anchor: 'end', color: '#ccc', font: {size: 9}, formatter: (value) => value === 0 ? '' : Math.round(value) }
                }  // Blue
            ];

            if (niftyData.length > 0) {
                datasets.push({
                    label: 'NIFTY',
                    type: 'line',
                    yAxisID: 'y1',
                    data: niftyData,
                    borderColor: '#ff9900',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.1
                });
            }

            let minNifty = null;
            let maxNifty = null;
            if (niftyData.length > 0) {
                const validNifty = niftyData.filter(v => v !== null && !isNaN(v));
                if (validNifty.length > 0) {
                    const absMin = Math.min(...validNifty);
                    const absMax = Math.max(...validNifty);
                    const diff = absMax - absMin;
                    const pad = diff * 0.1;
                    minNifty = Math.floor(absMin - pad);
                    maxNifty = Math.ceil(absMax + pad);
                }
            }

            const alternatingBackgroundPlugin = {
                id: 'alternatingBackgroundPlugin',
                beforeDraw: (chart) => {
                    const ctx = chart.canvas.getContext('2d');
                    const xAxis = chart.scales.x;
                    const yAxis = chart.scales.y;
                    ctx.save();
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
                    for (let i = 0; i < xAxis.ticks.length; i++) {
                        if (i % 2 === 1) { // Alternate days shading
                            const left = i === 0 ? xAxis.left : (xAxis.getPixelForTick(i) + xAxis.getPixelForTick(i-1)) / 2;
                            const right = i === xAxis.ticks.length - 1 ? xAxis.right : (xAxis.getPixelForTick(i) + xAxis.getPixelForTick(i+1)) / 2;
                            ctx.fillRect(left, yAxis.top, right - left, yAxis.bottom - yAxis.top);
                        }
                    }
                    ctx.restore();
                }
            };

            fiiDiiChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.dates,
                    datasets: datasets
                },
                plugins: [window.ChartDataLabels, alternatingBackgroundPlugin],
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: {
                        x: { stacked: false },
                        y: { stacked: false, position: 'left', grid: { color: '#333' } },
                        y1: {
                            type: 'linear', position: 'right', display: niftyData.length > 0, grid: { drawOnChartArea: false },
                            min: minNifty, max: maxNifty
                        }
                    },
                    plugins: {
                        legend: { labels: { color: '#ccc' } },
                        datalabels: {
                            display: true
                        }
                    }
                }
            });
        } catch (e) { console.error("Error loading FII/DII", e); }

        // 2. Load Participant OI Chart (Merged Daily Grouped Bar Chart - Contracts)
        const days = document.getElementById('market-activity-days').value || '30';
        try {
            const res = await fetch(`/api/market-activity/participant-oi?days=${days}`);
            const data = await res.json();

            // Build grouped ECharts for daily snapshot
            const container = document.getElementById('participant-oi-daily-summary');
            if (participantChartInstance) participantChartInstance.dispose();
            participantChartInstance = echarts.init(container);

            const dates = data.dates || [];
            if (dates.length === 0) {
                container.innerHTML = '<p style="text-align:center; color:#888;">No Participant OI data found.</p>';
                return;
            }

            // Define 6 metric categories per user request
            const metrics = [
                { key: 'fut_idx', label: 'Index Futures' },
                { key: 'fut_stk', label: 'Stock Futures' },
                { key: 'opt_idx_ce', label: 'Index Calls' },
                { key: 'opt_idx_pe', label: 'Index Puts' },
                { key: 'opt_stk_ce', label: 'Stock Calls' },
                { key: 'opt_stk_pe', label: 'Stock Puts' }
            ];

            const participants = [
                { key: 'fii', label: 'FII', color: '#E88B1E' },     // Orange
                { key: 'dii', label: 'DII', color: '#60a5fa' },     // Blue
                { key: 'pro', label: 'PRO', color: '#9B59B6' },     // Purple
                { key: 'client', label: 'CLI', color: '#60a5fa' },  // Green
                { key: 'smart_money', label: 'Smart Money (Inst+Pro)', color: '#FFD700' } // Yellow
            ];

            const xAxisData = metrics.map(m => m.label);

            // We only care about the latest date (Today)
            const todayIdx = dates.length - 1;

            const series = participants.map(p => {
                const pData = metrics.map(m => {
                    if (p.key === 'smart_money') {
                        // Calculate Smart Money: FII + DII + PRO (Excluding Client)
                        let sum = 0;
                        ['fii', 'dii', 'pro'].forEach(participantKey => {
                            const arrayKey = `${participantKey}_${m.key}`;
                            const arr = data[arrayKey] || [];
                            sum += arr.length > todayIdx ? arr[todayIdx] : 0;
                        });
                        return sum;
                    } else {
                        const arrayKey = `${p.key}_${m.key}`;
                        const arr = data[arrayKey] || [];
                        return arr.length > todayIdx ? arr[todayIdx] : 0;
                    }
                });

                return {
                    name: p.label,
                    type: 'bar',
                    barGap: '0%', // Combine bars closely together per instrument (no gap)
                    data: pData,
                    itemStyle: { color: p.color },
                    label: {
                        show: true,
                        position: 'top',
                        formatter: function(params) {
                            let val = params.value;
                            if (val === 0) return '';
                            let absVal = Math.abs(val);
                            if (absVal >= 100000) return (val / 100000).toFixed(1) + 'L';
                            if (absVal >= 1000) return (val / 1000).toFixed(1) + 'K';
                            return val;
                        },
                        color: '#ccc',
                        fontSize: 9
                    }
                };
            });

            const option = {
                backgroundColor: 'transparent',
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow',
                        shadowStyle: { color: 'rgba(255, 255, 255, 0.05)' } // Hover highlight per user request
                    }
                },
                legend: {
                    data: participants.map(p => p.label),
                    textStyle: { color: '#ccc' }
                },
                grid: { left: '3%', right: '4%', bottom: '10%', top: '15%', containLabel: true },
                xAxis: {
                    type: 'category',
                    data: xAxisData,
                    axisLabel: { color: '#ccc', fontWeight: 'bold' },
                    axisLine: { lineStyle: { color: '#333' } },
                    axisTick: { alignWithLabel: true }
                },
                yAxis: {
                    type: 'value',
                    axisLabel: { color: '#888' },
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
                    // Removed zebra striping splitArea per user request
                },
                series: series
            };

            participantChartInstance.setOption(option);

            // Granular Collective Chart (Today vs Previous Day)
            const granularContainer = document.getElementById('participant-oi-granular-summary');
            if (window.participantGranularChartInstance) window.participantGranularChartInstance.dispose();
            window.participantGranularChartInstance = echarts.init(granularContainer);

            const prevIdx = todayIdx > 0 ? todayIdx - 1 : 0;

            // Re-map the same participants for granular
            const granularSeries = participants.map(p => {
                const todayDataArr = metrics.map(m => {
                    if (p.key === 'smart_money') {
                        let sum = 0;
                        ['fii', 'dii', 'pro'].forEach(participantKey => {
                            const arr = data[`${participantKey}_${m.key}`] || [];
                            sum += arr.length > todayIdx ? arr[todayIdx] : 0;
                        });
                        return sum;
                    } else {
                        const arr = data[`${p.key}_${m.key}`] || [];
                        return arr.length > todayIdx ? arr[todayIdx] : 0;
                    }
                });

                const prevDataArr = metrics.map(m => {
                    if (p.key === 'smart_money') {
                        let sum = 0;
                        ['fii', 'dii', 'pro'].forEach(participantKey => {
                            const arr = data[`${participantKey}_${m.key}`] || [];
                            sum += arr.length > prevIdx ? arr[prevIdx] : 0;
                        });
                        return sum;
                    } else {
                        const arr = data[`${p.key}_${m.key}`] || [];
                        return arr.length > prevIdx ? arr[prevIdx] : 0;
                    }
                });

                return [
                    {
                        name: `${p.label} (Prev)`,
                        type: 'bar',
                        stack: p.label, // Stack Prev and Today for visual pairing if needed, or group
                        data: prevDataArr,
                        itemStyle: { color: p.key === 'smart_money' ? '#8B8000' : p.color, opacity: 0.5 }, // Dimmer for previous
                        label: { show: false }
                    },
                    {
                        name: `${p.label} (Today)`,
                        type: 'bar',
                        stack: p.label,
                        data: todayDataArr,
                        itemStyle: { color: p.color },
                        label: {
                            show: true,
                            position: 'top',
                            formatter: function(params) {
                                let val = params.value;
                                if (!val || val === 0) return '';
                                let absVal = Math.abs(val);
                                if (absVal >= 100000) return (val / 100000).toFixed(1) + 'L';
                                if (absVal >= 1000) return (val / 1000).toFixed(1) + 'K';
                                return val;
                            },
                            color: '#ccc',
                            fontSize: 9
                        }
                    }
                ];
            }).flat();

            // Add markArea to create shading for alternate groups
            // Removed zebra striping as it's visually distracting

            const granularOption = {
                backgroundColor: 'transparent',
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                legend: { type: 'scroll', textStyle: { color: '#ccc' }, bottom: 0 },
                grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
                xAxis: {
                    type: 'category',
                    data: xAxisData,
                    axisLabel: { color: '#ccc', fontWeight: 'bold' }
                },
                yAxis: {
                    type: 'value',
                    axisLabel: { color: '#888' },
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
                },
                series: granularSeries
            };

            window.participantGranularChartInstance.setOption(granularOption);


            // Trigger historical charts rendering next
            if (typeof renderParticipantHistorical === 'function') {
                renderParticipantHistorical(data);
            }

        } catch (e) { console.error("Error loading Participant OI", e); }

        // 2b. Load FII Money Terms Chart
        try {
            const res = await fetch(`/api/market-activity/fii-stats-money?days=${days}`);
            const data = await res.json();

            const container = document.getElementById('fii-money-daily-summary');
            if (window.fiiMoneyChartInstance) window.fiiMoneyChartInstance.dispose();
            window.fiiMoneyChartInstance = echarts.init(container);

            const dates = data.dates || [];
            if (dates.length === 0) {
                container.innerHTML = '<p style="text-align:center; color:#888;">No FII Statistics data found.</p>';
            } else {
                const xAxisData = ['Index Futures', 'Stock Futures', 'Index Options', 'Stock Options'];

                // Latest date data
                const todayIdx = dates.length - 1;
                const prevIdx = todayIdx > 0 ? todayIdx - 1 : 0;

                const todayData = [
                    data.fut_idx[todayIdx] || 0,
                    data.fut_stk[todayIdx] || 0,
                    data.opt_idx[todayIdx] || 0,
                    data.opt_stk[todayIdx] || 0
                ];

                const prevData = [
                    data.fut_idx[prevIdx] || 0,
                    data.fut_stk[prevIdx] || 0,
                    data.opt_idx[prevIdx] || 0,
                    data.opt_stk[prevIdx] || 0
                ];

                const option = {
                    backgroundColor: 'transparent',
                    tooltip: {
                        trigger: 'axis',
                        axisPointer: { type: 'shadow' }
                    },
                    legend: {
                        data: ['Previous Day', 'Today'],
                        textStyle: { color: '#ccc' }
                    },
                    grid: { left: '3%', right: '4%', bottom: '10%', top: '15%', containLabel: true },
                    xAxis: {
                        type: 'category',
                        data: xAxisData,
                        axisLabel: { color: '#ccc', fontWeight: 'bold' },
                        axisLine: { lineStyle: { color: '#333' } },
                        axisTick: { alignWithLabel: true }
                    },
                    yAxis: {
                        type: 'value',
                        axisLabel: { color: '#888', formatter: '₹ {value} Cr' },
                        splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
                    },
                    series: [
                        {
                            name: 'Previous Day',
                            type: 'bar',
                            data: prevData,
                            itemStyle: { color: '#60a5fa' }, // Blue
                            markArea: {
                                itemStyle: { color: 'rgba(255,255,255,0.05)' },
                                data: xAxisData.map((lbl, i) => {
                                    if (i % 2 === 1) return [{ xAxis: i - 0.5 }, { xAxis: i + 0.5 }];
                                    return null;
                                }).filter(d => d !== null)
                            },
                            label: { show: true, position: 'top', formatter: function(p) { return '₹' + p.value.toFixed(2) + 'Cr'; }, color: '#ccc', fontSize: 10 }
                        },
                        {
                            name: 'Today',
                            type: 'bar',
                            data: todayData,
                            itemStyle: { color: '#E88B1E' }, // Orange
                            label: { show: true, position: 'top', formatter: function(p) { return '₹' + p.value.toFixed(2) + 'Cr'; }, color: '#ccc', fontSize: 10 }
                        }
                    ]
                };
                window.fiiMoneyChartInstance.setOption(option);
            }
        } catch (e) { console.error("Error loading FII Money Terms", e); }

        // 3. Load EChart Multi-Axis
        const container = document.getElementById('echart-container');
        if (!echartInstance) {
            echartInstance = echarts.init(container, 'dark', { renderer: 'canvas' });
        }

        echartInstance.showLoading({ text: 'Loading Data...', color: '#60a5fa', textColor: '#fff', maskColor: 'rgba(30, 30, 30, 0.8)' });

        try {
            const res = await fetch(`/api/market-activity/dynamic-chart/${symbol}`);
            if (!res.ok) throw new Error("Data fetch failed");
            const data = await res.json();

            const option = {
                backgroundColor: 'transparent',
                tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                legend: { data: ['K-Line', 'MA20', 'Donchian Upper', 'Donchian Lower', 'Volume', 'ATR (14)', 'Future OI'] },
                grid: [
                    { left: '5%', right: '5%', height: '50%', top: '5%' }, // Main Chart
                    { left: '5%', right: '5%', top: '60%', height: '15%' }, // Volume
                    { left: '5%', right: '5%', top: '80%', height: '15%' }  // ATR / OI
                ],
                xAxis: [
                    { type: 'category', data: data.dates, gridIndex: 0, show: false },
                    { type: 'category', data: data.dates, gridIndex: 1, show: false },
                    { type: 'category', data: data.dates, gridIndex: 2 }
                ],
                yAxis: [
                    { scale: true, gridIndex: 0, splitLine: { show: true, lineStyle: { color: '#333' } } },
                    { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { formatter: (v) => (v/1000000).toFixed(1) + 'M' } },
                    { scale: true, gridIndex: 2, name: 'ATR %', splitNumber: 2, position: 'left' },
                    { scale: true, gridIndex: 2, name: 'Total OI', splitNumber: 2, position: 'right', axisLabel: { formatter: (v) => (v/1000000).toFixed(1) + 'M' } }
                ],
                dataZoom: [{ type: 'inside', xAxisIndex: [0, 1, 2], start: 50, end: 100 }, { show: true, type: 'slider', xAxisIndex: [0, 1, 2], bottom: '0%' }],
                series: [
                    { name: 'K-Line', type: 'candlestick', data: data.ohlc, itemStyle: { color: '#ef5350', color0: '#26a69a', borderColor: '#ef5350', borderColor0: '#26a69a' } },
                    { name: 'MA20', type: 'line', data: data.ma20, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#fff' } },
                    { name: 'Donchian Upper', type: 'line', data: data.donchian_upper, step: 'end', showSymbol: false, lineStyle: { type: 'dashed', color: '#ffeb3b', width: 1 } },
                    { name: 'Donchian Lower', type: 'line', data: data.donchian_lower, step: 'end', showSymbol: false, lineStyle: { type: 'dashed', color: '#ffeb3b', width: 1 } },
                    { name: 'Volume', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: data.volume, itemStyle: { color: '#5470c6' } },
                    { name: 'ATR (14)', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: data.atr, showSymbol: false, lineStyle: { color: '#fac858' } },
                    { name: 'Future OI', type: 'line', xAxisIndex: 2, yAxisIndex: 3, data: data.oi, showSymbol: false, lineStyle: { color: '#ee6666' } }
                ]
            };

            echartInstance.setOption(option, true);
        } catch (e) {
            container.innerHTML = `<div style="color:red; text-align:center; padding-top: 200px;">Error: ${e.message}</div>`;
        } finally {
            echartInstance?.hideLoading();
        }
    }

    // Listen for resize
    window.addEventListener('resize', () => {
        if (echartInstance) echartInstance.resize();
        if (window.fiiMoneyChartInstance) window.fiiMoneyChartInstance.resize();
        if (participantChartInstance) participantChartInstance.resize();
    });
// script end

let pcrChartInstance = null;
let highOiChartInstance = null;

async function loadOptionsAnalysis() {
    const symbol = document.getElementById('opt-analysis-symbol').value.toUpperCase();
    if (!symbol) return;

    // 1. Load 500-Day PCR Chart
    try {
        const res = await fetch(`/api/data/derivatives/pcr_history?symbol=${symbol}&days=500`);
        const data = await res.json();

        const chartDom = document.getElementById('opt-analysis-pcr-chart');
        if (pcrChartInstance) pcrChartInstance.dispose();
        pcrChartInstance = echarts.init(chartDom);

        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'cross' },
                formatter: function(params) {
                    let tooltipHtml = `<b>${params[0].axisValue}</b><br/>`;
                    params.forEach(param => {
                        let val = param.value !== undefined && param.value !== null ? parseFloat(param.value).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2}) : 'N/A';
                        if (param.seriesName.includes('%')) val += '%';
                        tooltipHtml += `${param.marker} ${param.seriesName}: <b>${val}</b><br/>`;
                    });
                    return tooltipHtml;
                }
            },
            legend: {
                data: ['Total OI', 'PCR', 'OI Chg %', 'Price Chg %', 'Price (FUT1)', 'ATM IV'],
                textStyle: { color: '#ccc' }
            },
            grid: [
                { left: '3%', right: '8%', height: '55%', top: '10%', containLabel: true }, // Main Chart
                { left: '3%', right: '8%', height: '15%', top: '70%', containLabel: true }  // ATM IV
            ],
            xAxis: [
                { type: 'category', data: data.dates, gridIndex: 0, show: false, axisPointer: {label: {show: false}} },
                { type: 'category', data: data.dates, gridIndex: 1, axisLabel: { color: '#888' }, axisLine: { lineStyle: { color: '#333' } } }
            ],
            yAxis: [
                { type: 'value', name: 'Total OI', position: 'left', gridIndex: 0, splitLine: { show: false }, axisLabel: { color: '#888' } },
                { type: 'value', name: 'Price', position: 'right', gridIndex: 0, splitLine: { lineStyle: { color: '#333', type: 'dashed' } }, scale: true, axisLabel: { color: '#888' } },
                { type: 'value', name: 'PCR', position: 'right', offset: 60, gridIndex: 0, scale: true, splitLine: { show: false }, axisLabel: { color: '#888' } },
                { type: 'value', name: '% Chg', position: 'right', offset: 120, gridIndex: 0, splitLine: { show: false }, axisLabel: { color: '#888', formatter: '{value}%' } },
                { type: 'value', name: 'ATM IV', gridIndex: 1, splitLine: { lineStyle: { color: '#333', type: 'dashed' } }, axisLabel: { color: '#888', formatter: '{value}%' } }
            ],
            dataZoom: [
                { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
                { type: 'slider', xAxisIndex: [0, 1], start: 50, end: 100, bottom: '2%', textStyle: { color: '#ccc' } }
            ],
            series: [
                { name: 'Total OI', type: 'bar', barGap: '0%', data: data.total_oi, itemStyle: { color: 'rgba(54, 162, 235, 0.4)' }, xAxisIndex: 0, yAxisIndex: 0 },
                { name: 'PCR', type: 'bar', barGap: '0%', data: data.pcr, itemStyle: { color: '#60a5fa' }, xAxisIndex: 0, yAxisIndex: 2 },
                { name: 'OI Chg %', type: 'bar', barGap: '0%', data: data.oi_chg_pct || [], itemStyle: { color: '#2196F3' }, xAxisIndex: 0, yAxisIndex: 3 },
                { name: 'Price Chg %', type: 'bar', barGap: '0%', data: data.price_chg_pct || [], itemStyle: { color: '#E88B1E' }, xAxisIndex: 0, yAxisIndex: 3 },
                { name: 'Price (FUT1)', type: 'line', data: data.price, itemStyle: { color: '#FFCC00' }, lineStyle: { width: 2 }, symbol: 'none', xAxisIndex: 0, yAxisIndex: 1 },
                { name: 'ATM IV', type: 'line', data: data.atm_iv || [], itemStyle: { color: '#e040fb' }, lineStyle: { width: 2, type: 'dashed' }, symbol: 'none', xAxisIndex: 1, yAxisIndex: 4 }
            ]
        };

        // Custom min/max to prevent flat lines
        if (data.price && data.price.length > 0) {
            const valid = data.price.filter(v => v !== null && !isNaN(v));
            if (valid.length > 0) {
                const min = Math.min(...valid);
                const max = Math.max(...valid);
                const pad = (max - min) * 0.1;
                option.yAxis[1].min = Math.floor(min - pad);
                option.yAxis[1].max = Math.ceil(max + pad);
            }
        }
        if (data.pcr && data.pcr.length > 0) {
            const valid = data.pcr.filter(v => v !== null && !isNaN(v));
            if (valid.length > 0) {
                const min = Math.min(...valid);
                const max = Math.max(...valid);
                const pad = (max - min) * 0.1;
                option.yAxis[2].min = (min - pad).toFixed(2);
                option.yAxis[2].max = (max + pad).toFixed(2);
            }
        }

        pcrChartInstance.setOption(option);

        // Render 10-day history table below the chart
        const tbody = document.getElementById('opt-analysis-history-body');
        if (tbody) {
            tbody.innerHTML = '';
            if (data.dates && data.dates.length > 0) {
                const latestDataPoints = Math.min(10, data.dates.length);
                const startIdx = data.dates.length - latestDataPoints;

                for (let i = data.dates.length - 1; i >= startIdx; i--) {
                    const tr = document.createElement('tr');
                    const d = data.dates[i];
                    const p = data.price[i];
                    const oi = data.total_oi[i];
                    const pcr = data.pcr[i];
                    const pChg = data.price_chg_pct ? data.price_chg_pct[i] : 0;
                    const oiChg = data.oi_chg_pct ? data.oi_chg_pct[i] : 0;
                    const iv = data.atm_iv ? data.atm_iv[i] : 0;

                    let pColor = pChg >= 0 ? '#60a5fa' : '#f44336';
                    let oColor = oiChg >= 0 ? '#60a5fa' : '#f44336';

                    tr.innerHTML = `
                        <td style="padding: 6px;">${d}</td>
                        <td style="padding: 6px;">${p ? p.toFixed(2) : '-'}</td>
                        <td style="padding: 6px; color: ${pColor};">${pChg !== undefined ? pChg.toFixed(2) + '%' : '-'}</td>
                        <td style="padding: 6px;">${oi ? oi.toLocaleString() : '-'}</td>
                        <td style="padding: 6px; color: ${oColor};">${oiChg !== undefined ? oiChg.toFixed(2) + '%' : '-'}</td>
                        <td style="padding: 6px;">${pcr ? pcr.toFixed(2) : '-'}</td>
                        <td style="padding: 6px;">${iv ? iv.toFixed(2) + '%' : '-'}</td>
                    `;
                    tbody.appendChild(tr);
                }
            } else {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#888;">No historical data available.</td></tr>';
            }
        }

    } catch (e) {
        console.error("Error loading PCR history:", e);
    }

    // Trigger load High OI Chart (Next step)
    if (typeof loadHighOI === 'function') {
        loadHighOI(symbol);
    }
}

async function loadHighOI(symbol) {
    try {
        const res = await fetch(`/api/data/derivatives/option_chain?symbol=${symbol}`);
        const data = await res.json();

        if (!data || !data.data || data.data.length === 0) {
            document.getElementById('opt-analysis-high-oi-chart').innerHTML = '<p style="text-align:center; color:#888;">No Option Chain data found.</p>';
            return;
        }

        const strikes = [];
        const ce_oi = [];
        const pe_oi = [];

        // Only take ATM +/- 20 strikes to avoid squished charts
        const sortedData = data.data.sort((a,b) => a.strike - b.strike);
        let atmIndex = 0;
        let minDiff = Infinity;

        for (let i = 0; i < sortedData.length; i++) {
            const diff = Math.abs(sortedData[i].strike - data.spot_price);
            if (diff < minDiff) {
                minDiff = diff;
                atmIndex = i;
            }
        }

        const startIdx = Math.max(0, atmIndex - 20);
        const endIdx = Math.min(sortedData.length, atmIndex + 20);
        const filteredData = sortedData.slice(startIdx, endIdx);

        filteredData.forEach(row => {
            strikes.push(row.strike);
            ce_oi.push(row.CE.oi || 0);
            pe_oi.push(row.PE.oi || 0);
        });

        const chartDom = document.getElementById('opt-analysis-high-oi-chart');
        if (highOiChartInstance) highOiChartInstance.dispose();
        highOiChartInstance = echarts.init(chartDom);

        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' },
                formatter: function (params) {
                    let res = `<div style="font-weight:bold;">Strike: ${params[0].axisValue}</div>`;
                    params.forEach(function (p) {
                        const val = Math.abs(p.value).toLocaleString();
                        res += `<div style="color:${p.color};">${p.seriesName}: ${val}</div>`;
                    });
                    return res;
                }
            },
            legend: {
                data: ['Call OI', 'Put OI'],
                textStyle: { color: '#ccc' }
            },
            grid: { left: '3%', right: '4%', bottom: '10%', top: '10%', containLabel: true },
            xAxis: {
                type: 'category',
                data: strikes,
                axisLabel: { color: '#FFCC00', fontWeight: 'bold', rotate: 45 },
                axisLine: { show: true, lineStyle: { color: '#333' } },
                axisTick: { show: false },
                splitLine: { show: true, lineStyle: { color: '#222' } }
            },
            yAxis: {
                type: 'value',
                axisLabel: {
                    color: '#888',
                    formatter: function (value) { return Math.abs(value); }
                },
                splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
            },
            series: [
                {
                    name: 'Call OI',
                    type: 'bar',
                    stack: 'Total',
                    label: { show: false },
                    itemStyle: { color: '#FF0000' }, // Classic Red for calls/resistance
                    data: ce_oi.map(v => -v) // Negative value to make it bar leftwards
                },
                {
                    name: 'Put OI',
                    type: 'bar',
                    stack: 'Total',
                    label: { show: false },
                    itemStyle: { color: '#60a5fa' }, // Classic Green for puts/support
                    data: pe_oi
                }
            ]
        };

        // Format tooltip to show absolute values for Call OI
        option.tooltip.formatter = function (params) {
            let res = `<div style="font-weight:bold;">Strike: ${params[0].axisValue}</div>`;
            params.forEach(function (p) {
                const val = Math.abs(p.value).toLocaleString();
                res += `<div style="color:${p.color};">${p.seriesName}: ${val}</div>`;
            });
            return res;
        };

        // Format xAxis to show absolute values
        option.xAxis.axisLabel.formatter = function (value) {
            return Math.abs(value);
        };

        highOiChartInstance.setOption(option);
    } catch (e) {
        console.error("Error loading high OI chart:", e);
    }
}

window.historicalChartInstances = window.historicalChartInstances || {};

function renderParticipantHistorical(data) {
    const dates = data.dates || [];
    if (dates.length === 0) return;

    // We have 6 metrics = 6 charts
    const metrics = [
        { key: 'fut_idx', id: 'lsRatioEchart-idx-fut', label: 'Index Futures' },
        { key: 'fut_stk', id: 'lsRatioEchart-stk-fut', label: 'Stock Futures' },
        { key: 'opt_idx_ce', id: 'lsRatioEchart-idx-call', label: 'Index Calls' },
        { key: 'opt_idx_pe', id: 'lsRatioEchart-idx-put', label: 'Index Puts' },
        { key: 'opt_stk_ce', id: 'lsRatioEchart-stk-call', label: 'Stock Calls' },
        { key: 'opt_stk_pe', id: 'lsRatioEchart-stk-put', label: 'Stock Puts' }
    ];

    const participants = [
        { key: 'fii', label: 'FII', color: '#E88B1E' },
        { key: 'dii', label: 'DII', color: '#60a5fa' },
        { key: 'pro', label: 'PRO', color: '#9B59B6' },
        { key: 'client', label: 'CLI', color: '#60a5fa' }
    ];

    metrics.forEach(m => {
        const dom = document.getElementById(m.id);
        if (!dom) return;

        if (window.historicalChartInstances[m.key]) window.historicalChartInstances[m.key].dispose();
        const chart = echarts.init(dom);
        window.historicalChartInstances[m.key] = chart;

        // Extract series per participant for this specific metric
        const series = participants.map(p => {
            const arr = data[`${p.key}_${m.key}`] || [];
            return {
                name: p.label,
                type: 'bar',
                data: arr,
                itemStyle: { color: p.color }
            };
        });

        const option = {
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
            legend: { data: participants.map(p => p.label), textStyle: { color: '#ccc' } },
            grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
            xAxis: {
                type: 'category',
                data: dates,
                axisLabel: { color: '#888' },
                axisLine: { lineStyle: { color: '#333' } }
            },
            yAxis: [
                {
                    type: 'value',
                    name: 'Ratio',
                    axisLabel: { color: '#888' },
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } },
                    nameTextStyle: { color: '#888' }
                },
                {
                    type: 'value',
                    name: 'NIFTY',
                    position: 'right',
                    axisLabel: { color: '#ccc' },
                    splitLine: { show: false },
                    nameTextStyle: { color: '#ccc' },
                    scale: true
                }
            ],
            dataZoom: [
                { type: 'inside', start: 50, end: 100 },
                { type: 'slider', start: 50, end: 100, textStyle: { color: '#ccc' } }
            ],
            series: series.map(s => {
                let sObj = { ...s };
                if (s.type === 'bar') {
                    sObj.label = {
                        show: true,
                        position: 'top',
                        formatter: function(params) {
                            let val = params.value;
                            if (!val || val === 0) return '';
                            let absVal = Math.abs(val);
                            if (absVal >= 100000) return (val / 100000).toFixed(1) + 'L';
                            if (absVal >= 1000) return (val / 1000).toFixed(1) + 'K';
                            return val;
                        },
                        color: '#ccc',
                        fontSize: 9
                    };
                }
                return {
                    ...sObj,
                    // Center the datum at 1 for the L/S Ratio so ratios < 1 point downward
                    markLine: {
                        data: [{ yAxis: 0 }], // Adjusted back to 0 as we use net positions now, not ratios
                        lineStyle: { color: '#444', type: 'solid', width: 2 },
                        symbol: 'none',
                        label: { show: false }
                    }
                };
            })
        };

        // ECharts has a specific property to set the datum line for bars
        option.series.forEach(s => { s.large = true; s.yAxisIndex = 0; });

        // Remove the manual min calculation which causes issues for negative numbers
        // option.yAxis[0].min = (value) => value.min < 0.5 ? 0 : value.min; // Give bottom room

        // Change datum to 1 instead of 0 for bars (since it's a ratio)
        option.series.forEach(s => { s.stack = null; });

        // Actually, the previous data arrays might be coming in as just net positions or large absolute numbers, not ratios centered around 1.
        // Wait, `data[..._fut_idx]` here comes from `/api/market-activity/participant-oi` which returns Net Positions (Long - Short), not ratios.
        // The net positions can be positive or negative natively.
        // We do NOT need to subtract 1 from these values.

        // Remove the data mapping since this is a Net Position chart, not an L/S Ratio chart.
        const transformedSeries = series.map(s => {
            return {
                ...s,
                data: s.data
            };
        });

        option.series = transformedSeries;

        // Let ECharts naturally scale Y-axis for Net Positions (which can be positive/negative)
        option.yAxis[0].min = null;

        // Add NIFTY overlay
        const niftyData = data.nifty_prices || data.nifty_close || [];
        if (niftyData.length > 0) {
            option.legend.data.push('NIFTY');
            option.series.push({
                name: 'NIFTY',
                type: 'line',
                data: niftyData,
                yAxisIndex: 1,
                itemStyle: { color: '#FFCC00' }, // Classic yellow line
                lineStyle: { width: 2 },
                symbol: 'none'
            });
        }

        // Relabel Y-axis to format absolute values for Net Position
        option.yAxis[0].axisLabel.formatter = function (value) {
            if (Math.abs(value) >= 1000) {
                return (value / 1000).toFixed(1) + 'k';
            }
            return value;
        };
        option.yAxis[0].name = "Net Pos (Qty)";

        // Fix the NIFTY line scaling so it isn't flat by forcing axis scale properties explicitly
        if (niftyData.length > 0) {
            const validNifty = niftyData.filter(v => v !== null && !isNaN(v));
            if (validNifty.length > 0) {
                const minNifty = Math.min(...validNifty);
                const maxNifty = Math.max(...validNifty);
                const diff = maxNifty - minNifty;
                const pad = diff > 0 ? diff * 0.1 : minNifty * 0.05; // Fix for identical values
                option.yAxis[1].min = Math.floor(minNifty - pad);
                option.yAxis[1].max = Math.ceil(maxNifty + pad);
                option.yAxis[1].scale = true; // Use ECharts scale but strictly bounded
            }
        } else {
            option.yAxis[1].scale = true;
        }

        // Remove the markline at 1 since Net Pos fluctuates around 0 naturally
        option.series.forEach(s => {
            if(s.markLine) {
                delete s.markLine;
            }
        });

        option.tooltip.formatter = function (params) {
            let res = `<div style="font-weight:bold;">${params[0].axisValue}</div>`;
            params.forEach(function (p) {
                if (p.seriesName === 'NIFTY') {
                    res += `<div style="color:${p.color};">${p.seriesName}: ${p.value.toLocaleString()}</div>`;
                } else {
                    res += `<div style="color:${p.color};">${p.seriesName}: ${p.value.toLocaleString()}</div>`;
                }
            });
            return res;
        };

        chart.setOption(option);
    });
}

let volPreExpiryChart = null;
let volConeChart = null;

async function loadVolatilityAnalysis() {
    const symbol = document.getElementById('vol-analysis-symbol').value.toUpperCase() || 'NIFTY';
    const expiryType = document.getElementById('vol-analysis-expiry-type').value;
    const lookback = document.getElementById('vol-analysis-lookback').value;
    const boxDays = document.getElementById('vol-analysis-box-days').value;

    // 1. Load Pre-Expiry Chart
    try {
        const preExpiryChartDom = document.getElementById('vol-pre-expiry-chart');
        if (volPreExpiryChart) volPreExpiryChart.dispose();
        volPreExpiryChart = echarts.init(preExpiryChartDom, 'dark', { renderer: 'canvas' });
        volPreExpiryChart.showLoading({ text: 'Loading...', color: '#60a5fa', maskColor: 'rgba(30, 30, 30, 0.8)' });

        const res = await fetch(`/api/data/derivatives/pre_expiry_action/${symbol}?lookback_days=${lookback}&box_days=${boxDays}&expiry_type=${expiryType}`);
        const data = await res.json();

        if (data.detail) {
            console.error("API Error Pre-Expiry:", data.detail);
            volPreExpiryChart.hideLoading();
            alert("Error loading Pre-Expiry Action: " + data.detail);
            return;
        }

        const markLines = (data.expiries || []).map(exp => {
            return { xAxis: exp, label: { formatter: 'Exp', position: 'start' } };
        });

        const markAreas = (data.boxes || []).map(box => {
            return [
                { xAxis: box.start_date, itemStyle: { color: 'rgba(255, 204, 0, 0.2)' } },
                { xAxis: box.end_date }
            ];
        });

        const preExpiryOption = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'cross' },
                formatter: function (params) {
                    let tooltipHtml = `<b>${params[0].axisValue}</b><br/>`;
                    let pChg = 0;
                    if(data.price_chg_pct_line && data.price_chg_pct_line[params[0].dataIndex] !== undefined) {
                         pChg = data.price_chg_pct_line[params[0].dataIndex];
                         tooltipHtml += `Price Change: <span style="color: ${pChg >= 0 ? '#60a5fa' : '#f44336'}">${pChg}%</span><br/>`;
                    }

                    params.forEach(param => {
                        let val = param.value !== undefined && param.value !== null ? parseFloat(param.value).toFixed(2) : 'N/A';
                        tooltipHtml += `${param.marker} ${param.seriesName}: <b>${val}</b><br/>`;
                    });
                    return tooltipHtml;
                }
            },
            legend: { data: ['Price', `Realized Vol (${boxDays}D)`, 'ATM IV', 'India VIX', 'Price Change %'], textStyle: { color: '#ccc' } },
            grid: { left: '3%', right: '3%', bottom: '10%', top: '15%', containLabel: true },
            xAxis: {
                type: 'category',
                data: data.dates,
                axisLabel: { color: '#888' },
                axisLine: { lineStyle: { color: '#333' } }
            },
            yAxis: [
                {
                    type: 'value',
                    name: 'Price',
                    position: 'left',
                    scale: true,
                    splitLine: { lineStyle: { color: '#333' } },
                    axisLabel: { color: '#ccc' },
                    nameTextStyle: { color: '#ccc' }
                },
                {
                    type: 'value',
                    name: `Vol / %`,
                    position: 'right',
                    scale: true,
                    splitLine: { show: false },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' }
                }
            ],
            dataZoom: [{ type: 'inside' }, { type: 'slider', textStyle: { color: '#ccc' } }],
            series: [
                {
                    name: 'Price Change %',
                    type: 'bar',
                    data: data.price_chg_pct_line,
                    yAxisIndex: 1,
                    itemStyle: {
                        color: function(params) {
                            return params.value >= 0 ? 'rgba(49, 118, 184, 0.5)' : 'rgba(244, 67, 54, 0.5)';
                        }
                    }
                },
                {
                    name: 'Price',
                    type: 'line',
                    data: data.prices,
                    yAxisIndex: 0,
                    itemStyle: { color: '#60a5fa' }, // Blue line for price
                    lineStyle: { width: 2 },
                    showSymbol: false,
                    markLine: {
                        symbol: ['none', 'none'],
                        lineStyle: { color: '#ff4444', type: 'solid', width: 1 },
                        data: markLines
                    },
                    markArea: {
                        data: markAreas
                    }
                },
                {
                    name: `Realized Vol (${boxDays}D)`,
                    type: 'line',
                    data: data.rv,
                    yAxisIndex: 1,
                    itemStyle: { color: '#E88B1E' }, // Orange line for RV
                    lineStyle: { width: 2 },
                    showSymbol: false
                },
                {
                    name: `ATM IV`,
                    type: 'line',
                    data: data.atm_iv_line,
                    yAxisIndex: 1,
                    itemStyle: { color: '#FF00FF' }, // Magenta line for ATM IV
                    lineStyle: { width: 1, type: 'dashed' },
                    symbol: 'circle',
                    symbolSize: 6,
                    showSymbol: true,
                    connectNulls: true
                },
                {
                    name: `India VIX`,
                    type: 'line',
                    data: data.india_vix_line,
                    yAxisIndex: 1,
                    itemStyle: { color: '#FFFF00' }, // Yellow line for VIX
                    lineStyle: { width: 1, type: 'dotted' },
                    symbol: 'circle',
                    symbolSize: 6,
                    showSymbol: true,
                    connectNulls: true
                }
            ]
        };

        volPreExpiryChart.setOption(preExpiryOption);
        volPreExpiryChart.hideLoading();
    } catch (e) {
        console.error("Error loading Pre-Expiry Action", e);
        if (volPreExpiryChart) volPreExpiryChart.hideLoading();
    }

    // 2. Load Volatility Cone Chart
    try {
        const coneChartDom = document.getElementById('vol-cone-chart');
        if (volConeChart) volConeChart.dispose();
        volConeChart = echarts.init(coneChartDom, 'dark', { renderer: 'canvas' });
        volConeChart.showLoading({ text: 'Loading...', color: '#60a5fa', maskColor: 'rgba(30, 30, 30, 0.8)' });

        const lookbackDays = document.getElementById('vol-analysis-lookback').value;
        const res = await fetch(`/api/data/derivatives/volatility_cone/${symbol}?lookback_days=${lookbackDays}`);
        const data = await res.json();

        if (data.detail) {
            console.error("API Error Vol Cone:", data.detail);
            volConeChart.hideLoading();
            alert("Error loading Volatility Cone: " + data.detail);
            return;
        }

        const coneOption = {
            backgroundColor: 'transparent',
            title: { text: 'Realized Volatility Cone', textStyle: { color: '#ccc', fontSize: 14 } },
            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
            legend: { data: ['Max', 'SD 2', 'SD 1', 'Mean', 'SD -1', 'SD -2', 'Min', 'Current RV', 'ATM IV', 'India VIX'], textStyle: { color: '#ccc' } },
            grid: { left: '3%', right: '3%', bottom: '5%', top: '15%', containLabel: true },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: data.windows.map(w => `${w}`), // Just the number
                name: 'Expiry Days',
                nameLocation: 'middle',
                nameGap: 30,
                axisLabel: { color: '#888' },
                axisLine: { lineStyle: { color: '#333' } }
            },
            yAxis: {
                type: 'value',
                scale: true,
                axisLabel: { formatter: '{value}%', color: '#ccc' },
                splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
            },
            series: [
                {
                    name: 'Max',
                    type: 'line',
                    data: data.max,
                    lineStyle: { color: '#60a5fa', width: 2 }, // Dark Blue
                    showSymbol: false
                },
                {
                    name: 'SD 2',
                    type: 'line',
                    data: data.sd_2,
                    lineStyle: { color: '#d32f2f', width: 2 }, // Red
                    showSymbol: false
                },
                {
                    name: 'SD 1',
                    type: 'line',
                    data: data.sd_1,
                    lineStyle: { color: '#7cb342', width: 2 }, // Green
                    showSymbol: false
                },
                {
                    name: 'Mean',
                    type: 'line',
                    data: data.mean,
                    lineStyle: { color: '#7b1fa2', width: 2 }, // Purple
                    showSymbol: false
                },
                {
                    name: 'SD -1',
                    type: 'line',
                    data: data.sd_minus_1,
                    lineStyle: { color: '#00acc1', width: 2 }, // Cyan
                    showSymbol: false
                },
                {
                    name: 'SD -2',
                    type: 'line',
                    data: data.sd_minus_2,
                    lineStyle: { color: '#f57c00', width: 2 }, // Orange
                    showSymbol: false
                },
                {
                    name: 'Min',
                    type: 'line',
                    data: data.min,
                    lineStyle: { color: '#8c9eff', width: 2 }, // Light Blue
                    showSymbol: false
                },
                {
                    name: 'Current RV',
                    type: 'line',
                    data: data.current_rv,
                    lineStyle: { color: '#E88B1E', width: 3, type: 'dashed' }, // Orange
                    itemStyle: { color: '#E88B1E' },
                    symbol: 'circle',
                    symbolSize: 6
                }
            ]
        };

        // Find the closest index mathematically because exact DTE might not match the fixed lookback array `[3, 7, 10...]`
        let dteIdx = -1;
        if (data.current_dte !== undefined && data.current_dte !== null) {
            let minDiff = Infinity;
            data.windows.forEach((w, idx) => {
                let diff = Math.abs(w - data.current_dte);
                if (diff < minDiff) {
                    minDiff = diff;
                    dteIdx = idx;
                }
            });
        }

        let atm_iv_data = data.atm_iv;
        if (data.atm_iv && data.atm_iv.length > 0) {
            coneOption.series.push({
                name: 'ATM IV',
                type: 'line',
                data: atm_iv_data,
                lineStyle: { color: '#FF00FF', width: 2, type: 'dashed' },
                itemStyle: { color: '#FF00FF' },
                symbol: 'circle',
                symbolSize: function(val, params) {
                    return params.dataIndex === dteIdx ? 10 : 0; // Only show prominent dot at DTE
                },
                showSymbol: true
            });
        }

        let vix_data = data.india_vix;
        if (data.india_vix && data.india_vix.length > 0) {
            coneOption.series.push({
                name: 'India VIX',
                type: 'line',
                data: vix_data,
                lineStyle: { color: '#FFFF00', width: 2, type: 'dotted' },
                itemStyle: { color: '#FFFF00' },
                symbol: 'circle',
                symbolSize: function(val, params) {
                    return params.dataIndex === dteIdx ? 10 : 0; // Only show prominent dot at DTE
                },
                showSymbol: true
            });
        }

        volConeChart.setOption(coneOption);
        volConeChart.hideLoading();
    } catch (e) {
        console.error("Error loading Volatility Cone", e);
        if (volConeChart) volConeChart.hideLoading();
    }
}

function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll('td, th');

        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, '').replace(/(\s\s)/gm, ' ');
            // Explicitly remove all variations of sorting arrows/junk characters that might exist
            data = data.replace(/[▼▲↕]/g, '').replace(/[\u25B2\u25BC\u2195]/g, '').trim();
            data = data.replace(/"/g, '""');
            row.push('"' + data + '"');
        }

        if (row.length > 0) {
            csv.push(row.join(','));
        }
    }

    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename + '.csv';
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

function exportChartDataToCSV(chartInstance, filename) {
    if (!chartInstance) {
        alert("Chart is not loaded or data is empty.");
        return;
    }

    // Handle Chart.js instances vs ECharts instances
    let isChartJS = typeof chartInstance.config !== 'undefined';
    let isECharts = typeof chartInstance.getOption === 'function';

    if (!isChartJS && !isECharts) {
        alert("Unsupported chart type.");
        return;
    }

    let csvRows = [];
    let headers = ['Date'];
    let seriesNames = [];
    let seriesData = [];
    let xAxisData = [];

    if (isECharts) {
        const option = chartInstance.getOption();
        if (!option) { alert("Error reading chart option"); return; }

        // ECharts Horizontal Bar charts store categories in yAxis
        // Need to check both yAxis array or single object format
        let yAxisObj = Array.isArray(option.yAxis) ? option.yAxis[0] : option.yAxis;
        let xAxisObj = Array.isArray(option.xAxis) ? option.xAxis[0] : option.xAxis;

        const isHorizontal = yAxisObj && yAxisObj.type === 'category' && yAxisObj.data;

        if (isHorizontal) {
            headers = ['Category'];
        }

        // Find xAxis data
        if (isHorizontal) {
            xAxisData = yAxisObj.data;
        } else if (xAxisObj && xAxisObj.data) {
            xAxisData = xAxisObj.data;
        } else if (option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
            // dataset fallback
            const src = option.dataset[0].source;
            if (Array.isArray(src) && src.length > 0) {
                // assume first row is headers, first col is dates
                xAxisData = src.slice(1).map(row => row[0]);
            }
        }

        if (option.series && option.series.length > 0) {
            option.series.forEach(s => {
                if (s.name) seriesNames.push(s.name);
                else seriesNames.push('Series');
                // Some charts might put data in dataset instead of directly in series
                if (s.data && s.data.length > 0) {
                    seriesData.push(s.data);
                } else if (option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
                    // Handled below, we'll wait for the dataset fallback
                } else {
                    seriesData.push([]);
                }
            });
        }

        // If series data is empty but we have a dataset source
        if (seriesData.length > 0 && seriesData[0].length === 0 && option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
            const src = option.dataset[0].source;
            if (Array.isArray(src) && src.length > 0) {
                // src[0] is headers, ignore [0][0] which is date
                for (let col = 1; col < src[0].length; col++) {
                    seriesNames[col - 1] = src[0][col] || `Series_${col}`;
                    let colData = [];
                    for (let r = 1; r < src.length; r++) {
                        colData.push(src[r][col]);
                    }
                    seriesData[col - 1] = colData;
                }
            }
        } else if (seriesData.length === 0 || (seriesData.length > 0 && seriesData[0].length === 0)) {
            // Check if there is data inside options.series regardless
            if (option.series && option.series.some(s => s.data && s.data.length > 0)) {
                // Proceed, data was successfully pushed
            } else {
                alert("No series data found in chart");
                return;
            }
        }
    } else if (isChartJS) {
        const data = chartInstance.data;
        if (!data || !data.datasets || data.datasets.length === 0) return;

        xAxisData = data.labels || [];

        data.datasets.forEach(s => {
            if (s.label) seriesNames.push(s.label);
            else seriesNames.push('Series');
            seriesData.push(s.data || []);
        });
    }

    // Build headers from series names
    seriesNames.forEach(name => {
        headers.push(`"${name}"`);
    });

    csvRows.push(headers.join(','));

    // Build rows
    const len = xAxisData.length > 0 ? xAxisData.length : (seriesData[0] ? seriesData[0].length : 0);

    for (let i = 0; i < len; i++) {
        let row = [];
        if (xAxisData.length > 0) {
            row.push(`"${xAxisData[i]}"`);
        } else {
            row.push(`"Row_${i}"`);
        }

        seriesData.forEach(d => {
            let val = '';
            if (d && d[i] !== undefined) {
                // Handle objects if data is complex (like candlesticks)
                if (typeof d[i] === 'object' && d[i] !== null) {
                    if (d[i].value !== undefined) {
                        val = d[i].value;
                    } else if (Array.isArray(d[i])) {
                        // For Candlesticks [open, close, min, max] or [date, val1, val2]
                        val = d[i].join('|');
                    }
                } else {
                    val = d[i];
                }
            }
            row.push(`"${val}"`);
        });

        csvRows.push(row.join(','));
    }

    const csvFile = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename + '.csv';
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}
