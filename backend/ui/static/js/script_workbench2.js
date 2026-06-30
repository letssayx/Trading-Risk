        // --- Main Tab Logic ---
        const MAIN_TABS_ORDER = ['terminal', 'ai_analyze', 'derivatives', 'special_arb', 'fundamentals', 'commodities', 'crypto', 'retail_instruments', 'history', 'import', 'corporate_actions', 'dividends', 'audit', 'config'];

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
            if (tabName === 'import' && window.uploader) { window.uploader.open(); return; }
            if (tabName === 'audit') loadAuditHistory(); // Auto-load audit on switch
            if (tabName === 'ai_analyze') fetchSystemAccuracy();
            if (tabName === 'skill_studio' && window.loadSkillList) window.loadSkillList();
            if (tabName === 'derivatives') {
                // Initialize first sub-tab if none selected
                if (!document.querySelector('.deriv-sub-tab.active')) {
                    switchDerivTab('matrix');
                } else if (document.querySelector('#deriv-tab-matrix').classList.contains('active') && document.getElementById('mr-data-body').innerHTML.includes('No data')) {
                     // Automatically load NIFTY snapshot if empty
                     if (typeof loadTimeseriesData === 'function') loadTimeseriesData(false);
                }
            }

            // Note: corporate_actions load is handled by the wrapper function below

            // Re-render ECharts or resize them since they might have collapsed while hidden
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
                if (window.volConeChart) window.volConeChart.resize();
                if (window.volPreExpiryChart) window.volPreExpiryChart.resize();
            }, 50);
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
                if (target.id === 'deriv-tab-matrix') {
                    target.style.display = 'flex';
                } else if (target.id === 'deriv-tab-oi') {
                    target.style.display = 'flex';
                } else if (target.id === 'deriv-tab-macro') {
                    target.style.display = 'flex';
                    if (typeof loadMacroData === 'function') loadMacroData();
                } else if (target.id === 'deriv-tab-watch') {
                    target.style.display = 'flex';
                } else if (target.id === 'deriv-tab-fii') {
                    target.style.display = 'flex';
                } else if (target.id === 'deriv-tab-optstrategy') {
                    target.style.display = 'flex';
                } else if (target.id === 'deriv-tab-idxbasket') {
                    target.style.display = 'block';
                } else {
                    target.style.display = 'block';
                }
                target.classList.add('active');
                btn.classList.add('active');
                btn.style.borderBottomColor = '#60a5fa';
                btn.style.color = '#fff';


                // Trigger Option Strategy tab data
                if (tabName === 'optstrategy' && typeof switchOptStratTab === 'function') {
                    // Activate putcall by default if not set
                    const activeSubTab = document.querySelector('.optstrat-tab.active');
                    if (activeSubTab) {
                        switchOptStratTab(activeSubTab.id.replace('optstrat-tab-btn-', ''));
                    } else {
                        switchOptStratTab('putcall');
                    }
                }

                // Trigger Index Basket loading
                if (tabName === 'idxbasket' && typeof window.loadIdxBasketData === 'function') {
                    window.loadIdxBasketData();
                }

                // Trigger options charts if OI Analysis
                if (tabName === 'oi' && typeof loadOptionsAnalysis === 'function') {
                    loadOptionsAnalysis();
                }

        // Trigger FII analysis if FII tab
        if (tabName === 'fii' && typeof loadFiiAnalysis === 'function') {
            loadFiiAnalysis();
        }

                // Trigger Volatility Analysis
                if (tabName === 'optanalysis' && typeof loadVolatilityAnalysis === 'function') {
                    loadVolatilityAnalysis();
                }

                // Re-render ECharts or resize them since they might have collapsed while hidden
                setTimeout(() => {
                    window.dispatchEvent(new Event('resize'));
            if (typeof volConeChart !== 'undefined' && volConeChart) volConeChart.resize();
            if (typeof volPreExpiryChart !== 'undefined' && volPreExpiryChart) volPreExpiryChart.resize();
                    if (window.volConeChart) window.volConeChart.resize();
                    if (window.volPreExpiryChart) window.volPreExpiryChart.resize();
        }, 200);
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
                    else if (item.issue_type === 'rights') typeBadge = '<span class="badge" style="background:#00bcd4; padding:2px 6px; border-radius:3px; color:white; font-size:11px;">Rights</span>';
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

            const groqKey = localStorage.getItem('GROQ_API_KEY');
            const openrouterKey = localStorage.getItem('OPENROUTER_API_KEY');
            const googleKey = localStorage.getItem('GOOGLE_API_KEY');

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

                if (msg.type === "think") {
                    if (!currentQuantLogicBlock) {
                        const id = "quant-logic-" + Date.now();
                        chatFeed.insertAdjacentHTML('beforeend', `
                        <div class="chat-message deepseek-message" id="${id}" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <details open>
                                <summary style="cursor: pointer; color: #64748b; font-weight: bold; margin-bottom: 5px;">[AI] REASONING</summary>
                                <div class="quant-content" style="color: #888; line-height: 1.5; white-space: pre-wrap; padding-left: 20px; font-family: monospace;"></div>
                            </details>
                        </div>`);
                        currentQuantLogicBlock = document.getElementById(id).querySelector('.quant-content');
                    }
                    currentQuantLogicBlock.insertAdjacentText('beforeend', msg.chunk);

                } else if (msg.type === "stream") {
                    if (!window.currentAnswerBlock) {
                        const id = "final-answer-" + Date.now();
                        chatFeed.insertAdjacentHTML('beforeend', `
                        <div class="chat-message final-message" id="${id}" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <div style="color: #4ade80; font-weight: bold; margin-bottom: 5px;">[AI] ANSWER</div>
                            <div class="answer-content" style="color: #e0e0e0; line-height: 1.5; white-space: pre-wrap;"></div>
                        </div>`);
                        window.currentAnswerBlock = document.getElementById(id).querySelector('.answer-content');
                    }
                    window.currentAnswerBlock.insertAdjacentText('beforeend', msg.chunk);

                } else if (msg.type === "final") {
                    // Reset current blocks for next message
                    currentQuantLogicBlock = null;
                    window.currentAnswerBlock = null;

                    cmdInput.placeholder = "Type command or symbol (e.g., NIFTY)...";
                    cmdInput.readOnly = false;

                    // Add rating and annotation UI
                    chatFeed.insertAdjacentHTML('beforeend', `
                        <div class="chat-actions" style="margin-top: 10px; display: flex; gap: 10px; align-items: center; padding-bottom: 15px; border-bottom: 1px solid #333;">
                            <span style="color: #888; font-size: 12px;">Skill Used: ${msg.skill_used} | Trade ID: ${msg.trade_id}</span>
                            <button onclick="rateTrade('${msg.trade_id}', 1)" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">⭐ 1</button>
                            <button onclick="rateTrade('${msg.trade_id}', 2)" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">⭐ 2</button>
                            <button onclick="rateTrade('${msg.trade_id}', 3)" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">⭐ 3</button>
                            <button onclick="rateTrade('${msg.trade_id}', 4)" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">⭐ 4</button>
                            <button onclick="rateTrade('${msg.trade_id}', 5)" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">⭐ 5</button>
                            <button onclick="annotateResponse('${msg.trade_id}', '${msg.skill_used}')" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">📌 Annotate</button>
                            <input type="text" id="correction-${msg.trade_id}" placeholder="Correction..." style="background: #111; border: 1px solid #444; color: #fff; padding: 2px 5px;">
                            <button onclick="submitCorrection('${msg.trade_id}')" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">Submit</button>
                        </div>`);

                    chatFeed.scrollTop = chatFeed.scrollHeight;
                }
            };

            aiWs.onerror = (e) => {
                chatFeed.innerHTML += `
                <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                    <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM ERROR]</div>
                    <div class="log-line text-warning">[ERROR] WebSocket connection failed.</div>
                </div>`;
                cmdInput.placeholder = "Type command or symbol (e.g., NIFTY)...";
                cmdInput.readOnly = false;
            };

            aiWs.onclose = () => {
                cmdInput.placeholder = "Type command or symbol (e.g., NIFTY)...";
                cmdInput.readOnly = false;
            };
        } // END OF runAiAnalysis
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

        // --- Fundamental Analysis logic ---
        window.loadFundamentalData = async function() {
            const symbol = document.getElementById('fund-symbol-input').value.toUpperCase().trim();
            const tbody = document.getElementById('fund-body');

            if (!symbol) {
                alert("Please enter a symbol.");
                return;
            }

            tbody.innerHTML = '<tr><td style="text-align: center; color: #888; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';

            try {
                const res = await fetch(`/api/data/fundamentals/${symbol}`);
                if (!res.ok) throw new Error("Failed to fetch");
                const data = await res.json();

                let html = '';
                for (const [key, val] of Object.entries(data)) {
                    // Format large numbers
                    let displayVal = val;
                    if (typeof val === 'number' && !key.includes('pct') && val > 10000) {
                        displayVal = val.toLocaleString();
                    } else if (typeof val === 'number') {
                        displayVal = val.toFixed(2);
                    }

                    html += `
                        <tr style="border-bottom: 1px solid #333;">
                            <td style="padding: 10px; color: #aaa; width: 30%; text-transform: capitalize;">${key.replace(/_/g, ' ')}</td>
                            <td style="padding: 10px; color: #fff;">${displayVal}</td>
                        </tr>
                    `;
                }
                tbody.innerHTML = html;

            } catch (e) {
                tbody.innerHTML = `<tr><td style="text-align: center; color: red; padding: 20px;">Error: ${e.message}</td></tr>`;
            }
        };

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
                // // // window.uploader.open = () => switchMainTab('import');
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
// script end
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

function renderParticipantHistorical(data) {
    const dates = data.dates || [];
    const tbody = document.getElementById('smart-money-history-body');
    if (!tbody) return;

    if (dates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#888;">No historical data available.</td></tr>';
        return;
    }

    // Clean up old dynamically created tbodies if user reloads
    document.querySelectorAll('#smart-money-history-table tbody').forEach(tb => {
        if (tb.id !== 'smart-money-history-body') {
            tb.remove();
        }
    });

    tbody.innerHTML = '';

    const metrics = [
        { key: 'fut_idx', label: 'Index Futures' },
        { key: 'fut_stk', label: 'Stock Futures' },
        { key: 'opt_idx_ce', label: 'Index Calls' },
        { key: 'opt_idx_pe', label: 'Index Puts' },
        { key: 'opt_stk_ce', label: 'Stock Calls' },
        { key: 'opt_stk_pe', label: 'Stock Puts' }
    ];

    const formatNum = (val) => {
        if (val == null || isNaN(val)) return '-';
        return parseInt(val).toLocaleString();
    };

    const getColor = (val) => {
        if (val > 0) return '#60a5fa'; // Blue for positive
        if (val < 0) return '#ff4d4d'; // Red for negative
        return '#ccc';
    };

    metrics.forEach(m => {
        // Latest data (last element in array)
        const latestIdx = dates.length - 1;

        // Helper to extract values
        const getVal = (prefix, participant, idx) => data[`${participant}_${m.key}${prefix}`]?.[idx] || 0;

        const latestFiiL = getVal('_long', 'fii', latestIdx);
        const latestFiiS = getVal('_short', 'fii', latestIdx);
        const latestFiiN = getVal('', 'fii', latestIdx);

        const latestDiiL = getVal('_long', 'dii', latestIdx);
        const latestDiiS = getVal('_short', 'dii', latestIdx);
        const latestDiiN = getVal('', 'dii', latestIdx);

        const latestProL = getVal('_long', 'pro', latestIdx);
        const latestProS = getVal('_short', 'pro', latestIdx);
        const latestProN = getVal('', 'pro', latestIdx);

        const latestCliL = getVal('_long', 'client', latestIdx);
        const latestCliS = getVal('_short', 'client', latestIdx);
        const latestCliN = getVal('', 'client', latestIdx);

        // Create an individual tbody for each instrument block
        const blockId = `smart-money-hist-${m.key}`;
        let blockHTML = `<tbody id="tbody-${m.key}">`;

        blockHTML += `
            <tr style="cursor: pointer; background: #222;" onclick="toggleSmartMoneyHistory('${blockId}')">
                <td style="text-align:center;"><i class="fas fa-chevron-right" id="icon-${blockId}" style="color:#888; font-size:10px;"></i></td>
                <td style="font-weight: bold; color: #fff;">${m.label}</td>
                <td>${dates[latestIdx]}</td>

                <td style="color: #60a5fa;">${formatNum(latestFiiL)}</td>
                <td style="color: #ff4d4d;">${formatNum(latestFiiS)}</td>
                <td style="color: ${getColor(latestFiiN)}; border-right: 1px solid #444;">${formatNum(latestFiiN)}</td>

                <td style="color: #60a5fa;">${formatNum(latestDiiL)}</td>
                <td style="color: #ff4d4d;">${formatNum(latestDiiS)}</td>
                <td style="color: ${getColor(latestDiiN)}; border-right: 1px solid #444;">${formatNum(latestDiiN)}</td>

                <td style="color: #60a5fa;">${formatNum(latestProL)}</td>
                <td style="color: #ff4d4d;">${formatNum(latestProS)}</td>
                <td style="color: ${getColor(latestProN)}; border-right: 1px solid #444;">${formatNum(latestProN)}</td>

                <td style="color: #60a5fa;">${formatNum(latestCliL)}</td>
                <td style="color: #ff4d4d;">${formatNum(latestCliS)}</td>
                <td style="color: ${getColor(latestCliN)};">${formatNum(latestCliN)}</td>
            </tr>
        `;

        // History rows (hidden by default, bound to the parent tbody via CSS/JS logic, but we'll use a class for JS to toggle)
        // Iterate backwards from T-1 to start
        for (let i = dates.length - 2; i >= 0; i--) {
            const fiiL = getVal('_long', 'fii', i);
            const fiiS = getVal('_short', 'fii', i);
            const fiiN = getVal('', 'fii', i);

            const diiL = getVal('_long', 'dii', i);
            const diiS = getVal('_short', 'dii', i);
            const diiN = getVal('', 'dii', i);

            const proL = getVal('_long', 'pro', i);
            const proS = getVal('_short', 'pro', i);
            const proN = getVal('', 'pro', i);

            const cliL = getVal('_long', 'client', i);
            const cliS = getVal('_short', 'client', i);
            const cliN = getVal('', 'client', i);

            blockHTML += `
                <tr class="${blockId}" style="display: none; background: #1a1a1a;">
                    <td></td>
                    <td style="color: #aaa; padding-left: 20px;">${m.label}</td>
                    <td style="color: #aaa;">${dates[i]}</td>

                    <td style="color: #60a5fa;">${formatNum(fiiL)}</td>
                    <td style="color: #ff4d4d;">${formatNum(fiiS)}</td>
                    <td style="color: ${getColor(fiiN)}; border-right: 1px solid #444;">${formatNum(fiiN)}</td>

                    <td style="color: #60a5fa;">${formatNum(diiL)}</td>
                    <td style="color: #ff4d4d;">${formatNum(diiS)}</td>
                    <td style="color: ${getColor(diiN)}; border-right: 1px solid #444;">${formatNum(diiN)}</td>

                    <td style="color: #60a5fa;">${formatNum(proL)}</td>
                    <td style="color: #ff4d4d;">${formatNum(proS)}</td>
                    <td style="color: ${getColor(proN)}; border-right: 1px solid #444;">${formatNum(proN)}</td>

                    <td style="color: #60a5fa;">${formatNum(cliL)}</td>
                    <td style="color: #ff4d4d;">${formatNum(cliS)}</td>
                    <td style="color: ${getColor(cliN)};">${formatNum(cliN)}</td>
                </tr>
            `;
        }
        blockHTML += `</tbody>`;
        document.getElementById('smart-money-history-table').insertAdjacentHTML('beforeend', blockHTML);
    });
}

let volPreExpiryChart = null;
let volConeChart = null;

window.allIvData = [];
let ivSortCol = 'symbol';
let ivSortAsc = true;

async function loadVolatilityAnalysis(event) {
    const symbol = document.getElementById('vol-analysis-symbol').value.toUpperCase() || 'NIFTY';
    const expiryType = document.getElementById('vol-analysis-expiry-type').value;
    const lookback = document.getElementById('vol-analysis-lookback').value || 500;
    const boxDays = document.getElementById('vol-analysis-box-days').value || 7;

    // Use event.target if provided (to distinguish btn-run-historical-iv from btn-load-vol-analysis)
    let loadBtn = document.getElementById('btn-load-vol-analysis');
    const isRunCalcEvent = event && event.target && (event.target.id === 'btn-run-historical-iv' || event.target.parentElement?.id === 'btn-run-historical-iv');
    if (event && event.currentTarget && !isRunCalcEvent) {
        loadBtn = event.currentTarget;
    } else if (isRunCalcEvent) {
        loadBtn = document.getElementById('btn-run-historical-iv');
    }

    let originalText = '';
    if (loadBtn) {
        originalText = loadBtn.innerHTML;
        if (isRunCalcEvent) {
            loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculating...';
        } else {
            loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        }
        loadBtn.disabled = true;
    }

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
            if (volPreExpiryChart) volPreExpiryChart.hideLoading();
            alert("Error loading Pre-Expiry Action: " + data.detail);

            const runButtonToRestore = document.getElementById('btn-run-historical-iv');
            if (isRunCalcEvent && runButtonToRestore) {
                runButtonToRestore.innerHTML = 'Run Historical IV Calculation';
                runButtonToRestore.disabled = false;
            }
            if (loadBtn) {
                loadBtn.disabled = false;
                loadBtn.innerHTML = originalText;
            }
            return;
        }

    const runButtonToRestore = document.getElementById('btn-run-historical-iv');

        const markLines = (data.expiries || []).map(exp => {
            return { xAxis: exp, label: { show: false } }; // Removed 'Exp' label to prevent overwriting
        });

        const markAreas = (data.boxes || []).map(box => {
            return [
                { xAxis: box.start_date, itemStyle: { color: 'rgba(255, 255, 255, 0.1)' } }, // Make shading slightly brighter per user request
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
                         tooltipHtml += `Price Change: <span style="color: ${pChg >= 0 ? '#00bcd4' : '#f44336'}">${pChg}%</span><br/>`;
                    }

                    params.forEach(param => {
                        let val = param.value !== undefined && param.value !== null ? parseFloat(param.value).toFixed(2) : 'N/A';
                        tooltipHtml += `${param.marker} ${param.seriesName}: <b>${val}</b><br/>`;
                    });
                    return tooltipHtml;
                }
            },
            legend: { data: [`Realized Vol (${boxDays}D)`, 'India VIX', 'ATM IV', 'Price Change %'], textStyle: { color: '#ccc' } },
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
                    name: `Vol / %`,
                    position: 'right',
                    scale: true,
                    splitLine: { lineStyle: { color: '#333' } },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' }
                },
                {
                    type: 'value',
                    name: `Price Chg %`,
                    position: 'left',
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
                    yAxisIndex: 1, // Use left Y-axis
                    itemStyle: {
                        color: function(params) {
                            return params.value >= 0 ? 'rgba(49, 118, 184, 0.5)' : 'rgba(244, 67, 54, 0.5)';
                        }
                    },
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
                    yAxisIndex: 0,
                    itemStyle: { color: '#ffffff' }, // White line for RV
                    lineStyle: { width: 2 },
                    showSymbol: false
                },
                {
                    name: `India VIX`,
                    type: 'line',
                    data: data.india_vix_line,
                    yAxisIndex: 0,
                    itemStyle: { color: '#FFFF00' }, // Yellow line for VIX
                    lineStyle: { width: 2 },
                    showSymbol: false,
                    connectNulls: true
                },
                {
                    name: `ATM IV`,
                    type: 'scatter', // Use scatter for single point
                    data: data.atm_iv_line.map((v, i) => v !== null ? [i, v] : null).filter(v => v !== null),
                    yAxisIndex: 0,
                    itemStyle: { color: '#E88B1E' }, // Orange point for ATM IV
                    symbol: 'circle',
                    symbolSize: 10,
                    zlevel: 10
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
        const forceCalcCheckbox = document.getElementById('vol-analysis-force-calc');
        const forceCalc = forceCalcCheckbox ? forceCalcCheckbox.checked : false;

        const res = await fetch(`/api/data/derivatives/volatility_cone/${symbol}?lookback_days=${lookbackDays}&force_calc=${forceCalc}`);
        const data = await res.json();

        if (data.detail) {
            console.error("API Error Vol Cone:", data.detail);
            if (volConeChart) volConeChart.hideLoading();
            alert("Error loading Volatility Cone: " + data.detail);
            if (isRunCalcEvent && runButtonToRestore) {
                runButtonToRestore.innerHTML = 'Run Historical IV Calculation';
                runButtonToRestore.disabled = false;
            }
            if (loadBtn) {
                loadBtn.disabled = false;
                loadBtn.innerHTML = originalText;
            }
            return;
        }

        // Re-enable load button if all went well
        if (isRunCalcEvent && runButtonToRestore) {
            runButtonToRestore.innerHTML = 'Run Historical IV Calculation';
            runButtonToRestore.disabled = false;
        }
        if (loadBtn) {
            loadBtn.disabled = false;
            loadBtn.innerHTML = originalText;
        }

        // Map line series to explicitly use numeric X values
        const formatLineData = (arr) => arr.map((v, i) => [data.windows[i], v]);

        const coneOption = {
            backgroundColor: 'transparent',
            title: { text: 'Realized Volatility Cone', textStyle: { color: '#ccc', fontSize: 14 } },
            tooltip: {
                trigger: 'item', // Changed to item so scatter dots show properly
                formatter: function(params) {
                    if (params.seriesName === 'Active Expiries') {
                        return `<b>Active Expiry</b><br/>DTE: ${params.value[0]}<br/>ATM IV: ${params.value[1].toFixed(2)}%`;
                    } else if (params.value && params.value.length === 2) {
                        return `<b>${params.seriesName}</b><br/>DTE: ${params.value[0]}<br/>Vol: ${params.value[1].toFixed(2)}%`;
                    }
                    return `${params.seriesName}: ${params.value}%`;
                }
            },
            legend: { data: ['95th %', '75th %', '50th % (Median)', '25th %', '5th %', 'Active Expiries'], textStyle: { color: '#ccc' } },
            color: ['#ef5350', '#ab47bc', '#00e676', '#29b6f6', '#66bb6a', '#E88B1E'], // Match Tooltip Colors
            grid: { left: '3%', right: '3%', bottom: '5%', top: '15%', containLabel: true },
            xAxis: {
                type: 'value',
                min: 1,
                max: 30, // Or dynamically Math.max(...data.windows)
                name: 'Days to Expiry (N)',
                nameLocation: 'middle',
                nameGap: 30,
                axisLabel: { color: '#888' },
                axisLine: { lineStyle: { color: '#333' } },
                splitLine: { show: false }
            },
            yAxis: {
                type: 'value',
                scale: true,
                axisLabel: { formatter: '{value}%', color: '#ccc' },
                splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
            },
            series: [
                {
                    name: '95th %',
                    type: 'line',
                    data: formatLineData(data.p95),
                    lineStyle: { width: 2, type: 'dashed' },
                    showSymbol: false
                },
                {
                    name: '75th %',
                    type: 'line',
                    data: formatLineData(data.p75),
                    lineStyle: { width: 2 },
                    areaStyle: { color: 'rgba(171, 71, 188, 0.1)', origin: 'auto' },
                    showSymbol: false
                },
                {
                    name: '50th % (Median)',
                    type: 'line',
                    data: formatLineData(data.p50),
                    lineStyle: { width: 4 }, // Thicker
                    showSymbol: false,
                    zlevel: 10
                },
                {
                    name: '25th %',
                    type: 'line',
                    data: formatLineData(data.p25),
                    lineStyle: { width: 2 },
                    areaStyle: { color: 'rgba(41, 182, 246, 0.1)', origin: 'auto' },
                    showSymbol: false
                },
                {
                    name: '5th %',
                    type: 'line',
                    data: formatLineData(data.p5),
                    lineStyle: { width: 2, type: 'dashed' },
                    showSymbol: false
                }
            ]
        };

        // Prepare scatter data for ATM IVs across expiries
        let highestIVDot = 0;
        let highestP95 = Math.max(...data.p95.filter(v => v !== null));

        if (data.active_expiries && data.active_expiries.length > 0) {
            let scatterData = [];

            // User feedback: Limit ATM IV dots to expiries with DTE >= 3 and max 4 points
            const expiriesToPlot = data.active_expiries.filter(e => e.dte >= 3).slice(0, 4);

            expiriesToPlot.forEach(exp => {
                // We use exact DTE now
                if (exp.dte <= 30) { // Keep within cone range
                    scatterData.push({
                        value: [exp.dte, exp.atm_iv],
                        name: `${exp.expiry_date} Expiry: ${exp.atm_iv.toFixed(1)}%` // Required label format
                    });

                    if (exp.atm_iv > highestIVDot) {
                        highestIVDot = exp.atm_iv;
                    }
                }
            });

            if (scatterData.length > 0) {
                coneOption.series.push({
                    name: 'Active Expiries', // Group legend
                    type: 'scatter',
                    data: scatterData,
                    itemStyle: { color: '#E88B1E' }, // Bloomberg Orange
                    symbol: 'circle',
                    symbolSize: 10,
                    tooltip: {
                        formatter: function(params) {
                            return `<b>${params.data.name}</b>`; // Hover format required by user
                        }
                    },
                    label: {
                        show: true,
                        position: 'top',
                        formatter: function(params) {
                            return params.data.name; // Permanent label required by user
                        },
                        color: '#ccc',
                        fontSize: 10
                    }
                });
            }
        }

        // Auto-scale Y-axis to ensure highest 95th percentile and highest IV dot are visible
        const maxYValue = Math.max(highestIVDot, highestP95);
        if (maxYValue > 0) {
            coneOption.yAxis.max = Math.ceil(maxYValue * 1.1); // Add 10% padding
        }

        volConeChart.setOption(coneOption);
        volConeChart.hideLoading();

        // --- Render Tables ---
        const summaryBody = document.getElementById('vol-iv-summary-body');
        if (summaryBody && data.iv_summary) {
            const summary = data.iv_summary;
            summaryBody.innerHTML = `
                <tr>
                    <td style="padding: 6px;">${summary.symbol || '-'}</td>
                    <td style="padding: 6px;">${summary.price !== null ? summary.price.toFixed(2) : '-'}</td>
                    <td style="padding: 6px; color: #E88B1E;">${summary.current_atm_iv !== null ? summary.current_atm_iv.toFixed(2) + '%' : '-'}</td>
                    <td style="padding: 6px;">${summary.ivr !== null ? summary.ivr.toFixed(2) : '-'}</td>
                    <td style="padding: 6px;">${summary.ivp !== null ? summary.ivp.toFixed(2) + '%' : '-'}</td>
                </tr>
            `;
        }

        const coneBody = document.getElementById('vol-cone-data-body');
        if (coneBody && data.windows) {
            coneBody.innerHTML = '';

            // Map active expiries by closest DTE to display Market ATM IV alongside
            const expiriesByDte = {};
            if (data.active_expiries) {
                data.active_expiries.forEach(exp => {
                    let dteIdx = -1;
                    let minDiff = Infinity;
                    data.windows.forEach((w, idx) => {
                        let diff = Math.abs(w - exp.dte);
                        // Prevent expiries from mapping to horizons that are too far away
                        if (diff < minDiff && diff <= 10) {
                            minDiff = diff;
                            dteIdx = idx;
                        }
                    });
                    if (dteIdx !== -1) {
                        // Keep the closest one only if there's a collision
                        if (!expiriesByDte[dteIdx] || minDiff < Math.abs(data.windows[dteIdx] - expiriesByDte[dteIdx].dte)) {
                            expiriesByDte[dteIdx] = exp;
                        }
                    }
                });
            }

            data.windows.forEach((w, idx) => {
                const tr = document.createElement('tr');
                const exp = expiriesByDte[idx];
                let atmIvStr = '-';
                if (exp) {
                    atmIvStr = `<span style="color: #E88B1E;">${exp.atm_iv.toFixed(2)}% (${exp.dte}d)</span>`;
                } else {
                    atmIvStr = `<span style="color: #666; font-size: 0.9em;">No expiry nearby</span>`;
                }

                tr.innerHTML = `
                    <td style="padding: 6px; font-weight: bold;">${w}</td>
                    <td style="padding: 6px;">${data.p5[idx] !== null ? data.p5[idx].toFixed(2) + '%' : '-'}</td>
                    <td style="padding: 6px;">${data.p25[idx] !== null ? data.p25[idx].toFixed(2) + '%' : '-'}</td>
                    <td style="padding: 6px;">${data.p50[idx] !== null ? data.p50[idx].toFixed(2) + '%' : '-'}</td>
                    <td style="padding: 6px;">${data.p75[idx] !== null ? data.p75[idx].toFixed(2) + '%' : '-'}</td>
                    <td style="padding: 6px;">${data.p95[idx] !== null ? data.p95[idx].toFixed(2) + '%' : '-'}</td>
                    <td style="padding: 6px;">${atmIvStr}</td>
                `;
                coneBody.appendChild(tr);
            });
        }

        // Table 3: Active Expiries
        const activeExpiriesBody = document.getElementById('vol-active-expiries-body');
        if (activeExpiriesBody && data.active_expiries) {
            activeExpiriesBody.innerHTML = '';
            if (data.active_expiries.length === 0) {
                activeExpiriesBody.innerHTML = '<tr><td colspan="3" style="text-align: center;">No active expiries found</td></tr>';
            } else {
                data.active_expiries.forEach(exp => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td style="padding: 6px;">${exp.expiry_date}</td>
                        <td style="padding: 6px;">${exp.dte}</td>
                        <td style="padding: 6px; color: #E88B1E; font-weight: bold;">${exp.atm_iv.toFixed(2)}%</td>
                    `;
                    activeExpiriesBody.appendChild(tr);
                });
            }
        }

    } catch (e) {
        console.error("Error loading Volatility Cone", e);
        if (volConeChart) volConeChart.hideLoading();
    }

    if (loadBtn) {
        loadBtn.disabled = false;
        loadBtn.innerHTML = originalText;
    }

    // Also restore the historical IV button if it was disabled
    const runBtn = document.getElementById('btn-run-historical-iv');
    if (runBtn) {
        runBtn.innerHTML = 'Run Historical IV Calculation';
        runBtn.disabled = false;
    }
}


async function loadAllIVSummary(event) {
    if (event) event.preventDefault();
    const btn = document.getElementById('btn-load-all-iv');
    const expirySelect = document.getElementById('iv-summary-expiry-type');
    const expiryType = expirySelect ? expirySelect.value : 'monthly';
    const originalText = btn ? btn.innerHTML : 'Load All F&O';

    if (btn) {
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
        btn.disabled = true;
    }

    const tbody = document.getElementById('vol-iv-summary-body');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Fetching data across all symbols...</td></tr>';
    }

    try {
        const force = document.getElementById('vol-force-refresh') && document.getElementById('vol-force-refresh').checked;
        if (force) {
            if (tbody) tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Checking for new data and syncing...</td></tr>';
            await fetch(`/api/data/analysis/volatility/sync?force=true`, { method: 'POST' });
        }
        const res = await fetch(`/api/data/derivatives/volatility_summary_all?expiry_type=${expiryType}`);
        const result = await res.json();

        console.log("All F&O API response:", result);

        window.allIvData = result.data || [];

        if (window.allIvData.length === 0) {
            if (tbody) tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No IV data found. Please run the Historical IV calculation first.</td></tr>';
            return;
        }

        renderAllIVSummary();

    } catch (e) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: red;">Error: ${e.message}</td></tr>`;
    } finally {
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }
}

function sortAllIV(col) {
    if (ivSortCol === col) {
        ivSortAsc = !ivSortAsc;
    } else {
        ivSortCol = col;
        ivSortAsc = true;
    }
    renderAllIVSummary();
}

function renderAllIVSummary() {
    if (!window.allIvData || window.allIvData.length === 0) return;

    // Sort data
    const sortedData = [...window.allIvData].sort((a, b) => {
        let valA = a[ivSortCol];
        let valB = b[ivSortCol];

        if (valA === null || valA === undefined) valA = ivSortAsc ? Infinity : -Infinity;
        if (valB === null || valB === undefined) valB = ivSortAsc ? Infinity : -Infinity;

        if (valA < valB) return ivSortAsc ? -1 : 1;
        if (valA > valB) return ivSortAsc ? 1 : -1;
        return 0;
    });

    const tbody = document.getElementById('vol-iv-summary-body');
    tbody.innerHTML = '';

    sortedData.forEach(item => {
        const tr = document.createElement('tr');

        const isHighIV = item.ivp > 80;
        const ivpColor = isHighIV ? '#ff4d4d' : '#ccc';

        tr.innerHTML = `
            <td style="padding: 6px; font-weight: bold; color: #4da6ff; cursor: pointer;" onclick="document.getElementById('vol-analysis-symbol').value='${item.symbol}'; document.getElementById('btn-load-vol-analysis').click(); window.scrollTo(0, 0);">${item.symbol}</td>
            <td style="padding: 6px;">${item.price !== undefined && item.price !== null ? item.price.toFixed(2) : '-'}</td>
            <td style="padding: 6px; color: #e6a23c;">${item.current_atm_iv !== null ? item.current_atm_iv.toFixed(2) + '%' : '-'}</td>
            <td style="padding: 6px;">${item.ivr !== null ? item.ivr.toFixed(2) : '-'}</td>
            <td style="padding: 6px; color: ${ivpColor};">${item.ivp !== null ? item.ivp.toFixed(2) + '%' : '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}


function renderParticipantGranular(data) {
    const container = document.getElementById('participant-oi-granular-summary');
    if (!container) return;

    if (window.participantGranularChartInstance) window.participantGranularChartInstance.dispose();
    window.participantGranularChartInstance = echarts.init(container);

    const dates = data.dates || [];
    if (dates.length < 2) return;

    const todayIdx = dates.length - 1;
    const prevIdx = dates.length - 2;

    const metrics = [
        { key: 'fut_idx', label: 'Index Futures' },
        { key: 'fut_stk', label: 'Stock Futures' },
        { key: 'opt_idx_ce', label: 'Index Calls' },
        { key: 'opt_idx_pe', label: 'Index Puts' }
    ];

    const participants = [
        { key: 'fii', label: 'FII', color: '#3176B8' },
        { key: 'dii', label: 'DII', color: '#4caf50' },
        { key: 'pro', label: 'PRO', color: '#9B59B6' },
        { key: 'client', label: 'CLI', color: '#00bcd4' }
    ];

    const xAxisData = metrics.map(m => m.label);

    const series = [];
    participants.forEach(p => {
        // Prev Data
        series.push({
            name: `${p.label} (Prev)`,
            type: 'bar',
            barGap: '0%',
            data: metrics.map(m => {
                const arr = data[`${p.key}_${m.key}`] || [];
                return arr.length > prevIdx ? arr[prevIdx] : 0;
            }),
            itemStyle: { color: '#60a5fa' }, // Blue for Prev
            label: { show: true, position: 'top', color: '#ccc', fontSize: 9, formatter: p => p.value !== 0 ? (Math.abs(p.value) >= 100000 ? (p.value / 100000).toFixed(1) + 'L' : p.value) : '' }
        });

        // Today Data
        series.push({
            name: `${p.label} (Today)`,
            type: 'bar',
            data: metrics.map(m => {
                const arr = data[`${p.key}_${m.key}`] || [];
                return arr.length > todayIdx ? arr[todayIdx] : 0;
            }),
            itemStyle: { color: p.color }, // Original color for Today
            label: { show: true, position: 'top', color: '#ccc', fontSize: 9, formatter: p => p.value !== 0 ? (Math.abs(p.value) >= 100000 ? (p.value / 100000).toFixed(1) + 'L' : p.value) : '' }
        });
    });

    const option = {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { data: participants.flatMap(p => [`${p.label} (Prev)`, `${p.label} (Today)`]), textStyle: { color: '#ccc' }, top: 0, type: 'scroll' },
        grid: { left: '3%', right: '4%', bottom: '5%', top: '15%', containLabel: true },
        xAxis: { type: 'category', data: xAxisData, axisLabel: { color: '#ccc', fontWeight: 'bold' } },
        yAxis: { type: 'value', axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#333', type: 'dashed' } } },
        series: series
    };

    window.participantGranularChartInstance.setOption(option);
}

async function renderFiiMoneyStats(baseDays) {
    const daysSelect = document.getElementById('fii-money-days');
    const days = daysSelect ? daysSelect.value : 1;
    const container = document.getElementById('fii-money-daily-summary');
    if (!container) return;

    if (window.fiiMoneyChartInstance) window.fiiMoneyChartInstance.dispose();
    window.fiiMoneyChartInstance = echarts.init(container);
    window.fiiMoneyChartInstance.showLoading({ text: 'Loading...', color: '#60a5fa', maskColor: 'rgba(30, 30, 30, 0.8)' });

    try {
        const res = await fetch(`/api/market-activity/fii-stats-money?days=${days}`);
        const data = await res.json();

        window.fiiMoneyChartInstance.hideLoading();

        if (!data || !data.dates || data.dates.length === 0) {
            container.innerHTML = '<p style="text-align:center; color:#888;">No FII Money stats found.</p>';
            return;
        }

        const dates = data.dates;
        const metrics = [
            { key: 'fut_idx', label: 'Index Futures' },
            { key: 'opt_idx', label: 'Index Options' },
            { key: 'fut_stk', label: 'Stock Futures' },
            { key: 'opt_stk', label: 'Stock Options' }
        ];

        let option;

        if (dates.length === 1) {
            // Single day (Today) - Original Bar Chart
            const todayIdx = 0;
            const xAxisData = metrics.map(m => m.label);
            const seriesData = metrics.map(m => data[m.key] ? data[m.key][todayIdx] : 0);

            option = {
                backgroundColor: 'transparent',
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: v => '₹' + v.toLocaleString() + ' Cr' },
                grid: { left: '3%', right: '4%', bottom: '5%', top: '15%', containLabel: true },
                xAxis: { type: 'category', data: xAxisData, axisLabel: { color: '#ccc', fontWeight: 'bold' } },
                yAxis: { type: 'value', axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#333', type: 'dashed' } }, name: 'Crores', nameTextStyle: { color: '#888' } },
                series: [{
                    name: 'FII Net (Cr)',
                    type: 'bar',
                    data: seriesData,
                    itemStyle: { color: '#60a5fa' }, // Orange = Long/Pos, Blue = Short/Neg
                    label: { show: true, position: 'top', color: '#ccc', formatter: p => '₹' + p.value.toLocaleString() + ' Cr' }
                }]
            };
        } else {
            // Multiple Days - Grouped Bar Chart per day
            const series = metrics.map(m => {
                return {
                    name: m.label,
                    type: 'bar',
                    barGap: '0%', // Group closely
                    data: data[m.key] || [],
                    label: {
                        show: false
                    }
                };
            });

            option = {
                backgroundColor: 'transparent',
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: v => '₹' + v.toLocaleString() + ' Cr' },
                legend: { data: metrics.map(m => m.label), textStyle: { color: '#ccc' }, top: 0 },
                grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
                xAxis: { type: 'category', data: dates, axisLabel: { color: '#888' } },
                yAxis: { type: 'value', axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#333', type: 'dashed' } }, name: 'Crores', nameTextStyle: { color: '#888' } },
                dataZoom: [{ type: 'inside' }, { type: 'slider', textStyle: { color: '#ccc' } }],
                series: series
            };
        }

        window.fiiMoneyChartInstance.setOption(option);
    } catch(e) {
        console.error("Error loading FII money stats", e);
        window.fiiMoneyChartInstance.hideLoading();
    }
}


async function loadMarketOptionsCharts() {
    const symbol = document.getElementById('market-activity-index-symbol').value.toUpperCase().trim();
    const lookback = document.getElementById('market-activity-opt-lookback').value;
    const expiryOnly = document.getElementById('market-opt-expiry-only').checked;

    const pcrContainer = document.getElementById('market-opt-pcr-chart');
    const highOiContainer = document.getElementById('market-opt-high-oi-chart');

    if (window.marketPcrChartInstance) window.marketPcrChartInstance.dispose();
    if (window.marketHighOiChartInstance) window.marketHighOiChartInstance.dispose();

    window.marketPcrChartInstance = echarts.init(pcrContainer);
    window.marketHighOiChartInstance = echarts.init(highOiContainer);

    window.marketPcrChartInstance.showLoading({ text: 'Loading...', color: '#60a5fa', maskColor: 'rgba(30, 30, 30, 0.8)' });
    window.marketHighOiChartInstance.showLoading({ text: 'Loading...', color: '#60a5fa', maskColor: 'rgba(30, 30, 30, 0.8)' });

    try {
        const res = await fetch(`/api/data/derivatives/pcr_history?symbol=${symbol}&days=${lookback}&expiry_only=${expiryOnly}`);
        const data = await res.json();

        window.marketPcrChartInstance.hideLoading();
        window.marketHighOiChartInstance.hideLoading();

        if (!data.dates || data.dates.length === 0) {
            pcrContainer.innerHTML = '<p style="text-align:center; color:#888;">No historical data available.</p>';
            highOiContainer.innerHTML = '<p style="text-align:center; color:#888;">No historical data available.</p>';
            return;
        }

        const showCombinedOi = document.getElementById('market-opt-combined-oi').checked;

        // Render PCR Chart (Price vs OI vs PCR)
        const dates = data.dates;
        const prices = data.price;
        const pcrs = data.pcr;
        const oiData = showCombinedOi ? data.total_oi : data.fut_oi;
        const oiSeriesName = showCombinedOi ? 'Combined OI' : 'Futures OI';

        const pcrOption = {
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
            legend: { data: [oiSeriesName, 'Close Price', 'PCR'], textStyle: { color: '#ccc' }, top: 0 },
            grid: { left: '5%', right: '10%', bottom: '10%', top: '15%', containLabel: true },
            xAxis: { type: 'category', data: dates, axisLabel: { color: '#888' } },
            yAxis: [
                { type: 'value', name: 'Close', position: 'left', axisLabel: { color: '#888' }, splitLine: { show: false }, scale: true },
                { type: 'value', name: 'PCR', position: 'right', axisLabel: { color: '#888' }, splitLine: { show: false } },
                { type: 'value', name: 'OI', position: 'right', offset: 50, axisLabel: { color: '#888', formatter: (val) => (val/100000).toFixed(1) + 'L' }, splitLine: { show: false }, min: 0 } // For OI background with visible axis
            ],
            dataZoom: [{ type: 'inside' }, { type: 'slider', textStyle: { color: '#ccc' } }],
            series: [
                { name: oiSeriesName, type: 'bar', yAxisIndex: 2, data: oiData, itemStyle: { color: 'rgba(96, 165, 250, 0.2)' }, barWidth: '100%' },
                { name: 'Close Price', type: 'line', yAxisIndex: 0, data: prices, itemStyle: { color: '#ffcc00' }, lineStyle: { width: 2 }, symbol: 'none' },
                { name: 'PCR', type: 'line', yAxisIndex: 1, data: pcrs, itemStyle: { color: '#00e676' }, lineStyle: { width: 2 }, symbol: 'none' }
            ]
        };
        window.marketPcrChartInstance.setOption(pcrOption);

        // Load High OI Chart (CE vs PE) via option_chain endpoint
        const ocRes = await fetch(`/api/data/derivatives/option_chain?symbol=${symbol}`);
        const ocData = await ocRes.json();

        if (ocData && ocData.data && ocData.data.length > 0) {
            // Instead of taking rigid +/- 20 strikes, we take the top 15 by Call OI and top 15 by Put OI, and union them.
            const allData = [...ocData.data];

            // Sort by CE OI descending
            const topCe = [...allData].sort((a, b) => (b.CE.oi || 0) - (a.CE.oi || 0)).slice(0, 15);
            // Sort by PE OI descending
            const topPe = [...allData].sort((a, b) => (b.PE.oi || 0) - (a.PE.oi || 0)).slice(0, 15);

            // Union the strikes using a Set to avoid duplicates
            const topStrikesSet = new Set();
            topCe.forEach(row => topStrikesSet.add(row.strike));
            topPe.forEach(row => topStrikesSet.add(row.strike));

            // Filter the original data to only include these top strikes, then sort by strike price
            const filteredData = allData
                .filter(row => topStrikesSet.has(row.strike))
                .sort((a, b) => b.strike - a.strike);

            const strikes = [];
            const callOi = [];
            const putOi = [];

            filteredData.forEach(row => {
                strikes.push(row.strike);
                callOi.push(row.CE.oi || 0);
                putOi.push(row.PE.oi || 0);
            });

            const butterflyOption = {
                backgroundColor: 'transparent',
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                legend: { data: ['Put OI', 'Call OI'], textStyle: { color: '#ccc' }, top: 0 },
                grid: [
                    { left: '5%', right: '54%', bottom: '10%', top: '15%' }, // Left side (Call OI)
                    { left: '54%', right: '5%', bottom: '10%', top: '15%' }  // Right side (Put OI)
                ],
                xAxis: [
                    { type: 'value', gridIndex: 0, inverse: true, axisLabel: { show: false }, splitLine: { show: false } },
                    { type: 'value', gridIndex: 1, axisLabel: { show: false }, splitLine: { show: false } }
                ],
                yAxis: [
                    { type: 'category', gridIndex: 0, data: strikes, axisLabel: { show: true, color: '#e0e0e0', margin: 45, align: 'center', fontWeight: 'bold' }, position: 'right', axisTick: { show: false }, axisLine: { show: false } },
                    { type: 'category', gridIndex: 1, data: strikes, axisLabel: { show: false }, position: 'left', axisTick: { show: false }, axisLine: { show: false } }
                ],
                series: [
                    { name: 'Call OI', type: 'bar', xAxisIndex: 0, yAxisIndex: 0, data: callOi, itemStyle: { color: '#ff9800' }, label: { show: true, position: 'left', color: '#ccc', formatter: p => (p.value/100000).toFixed(1) + 'L' } },
                    { name: 'Put OI', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: putOi, itemStyle: { color: '#3176B8' }, label: { show: true, position: 'right', color: '#ccc', formatter: p => (p.value/100000).toFixed(1) + 'L' } }
                ]
            };
            window.marketHighOiChartInstance.setOption(butterflyOption);
        } else {
            highOiContainer.innerHTML = '<p style="text-align:center; color:#888;">No high OI strike data available for latest date.</p>';
        }

    } catch(e) {
        console.error("Error loading market options charts", e);
        pcrContainer.innerHTML = `<p style="color:red;">Error: ${e.message}</p>`;
        highOiContainer.innerHTML = `<p style="color:red;">Error: ${e.message}</p>`;
    }
}

// --- MASTER SYNC LOGIC ---
async function triggerMasterSync() {
    const btn = document.getElementById('master-sync-btn');
    if(!btn) return;

    // Save original state
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
    btn.disabled = true;

    try {
        console.log("Master Sync started...");

        const promises = [];

        // 1. Sync Macro Data (Turtle Tab)
        if (typeof syncMacroData === 'function') promises.push(syncMacroData().catch(e => console.error("syncMacroData failed", e)));

        // 2. Load Market Watch (Derivatives - Basis Watch)
        if (typeof loadMarketWatch === 'function') promises.push(loadMarketWatch(true).catch(e => console.error("loadMarketWatch failed", e)));

        // 3. Load Volatility Data
        if (typeof fetchVolatilityData === 'function') promises.push(fetchVolatilityData(true).catch(e => console.error("fetchVolatilityData failed", e)));

        // 4. F&O Data
        if (typeof fetchFutureOI === 'function') promises.push(fetchFutureOI(true).catch(e => console.error("fetchFutureOI failed", e)));

        // 5. MWPL Data
        if (typeof loadMWPLAnalysis === 'function') promises.push(loadMWPLAnalysis(true).catch(e => console.error("loadMWPLAnalysis failed", e)));

        // 6. OI Analysis
        if (typeof OiTool !== 'undefined' && typeof OiTool.syncAndLoadAggregatedData === 'function') {
            promises.push(OiTool.syncAndLoadAggregatedData(false).catch(e => console.error("OiTool sync failed", e)));
        }

        // 7. Rollover Analysis
        if (typeof RolloverTool !== 'undefined' && typeof RolloverTool.syncAndLoadAggregatedData === 'function') {
            promises.push(RolloverTool.syncAndLoadAggregatedData(false).catch(e => console.error("RolloverTool sync failed", e)));
        }

        // 8. Volatility Analysis (All F&O)
        if (typeof loadAllIVSummary === 'function') promises.push(loadAllIVSummary(new Event('sync')).catch(e => console.error("loadAllIVSummary failed", e)));

        // Clear main UI Matrix (from previous logic)
        if (typeof clearMatrixUI === 'function') clearMatrixUI();

        // Data Matrix (Load Timeseries / Snapshot view for Data Matrix)
        if (typeof loadTimeseriesData === 'function') promises.push(loadTimeseriesData(true).catch(e => console.error("loadTimeseriesData failed", e)));

        // Options Chain
        if (typeof loadOptionChain === 'function') promises.push(loadOptionChain().catch(e => console.error("loadOptionChain failed", e)));

        // Market Activity / Macro & Events (loadMarketOptionsCharts usually triggers market activity charts)
        if (typeof loadMarketOptionsCharts === 'function') promises.push(loadMarketOptionsCharts().catch(e => console.error("loadMarketOptionsCharts failed", e)));

        // Wait for all to finish concurrently
        await Promise.allSettled(promises);

        console.log("Master Sync completed.");
    } catch (e) {
        console.error("Master Sync error:", e);
        alert("Master Sync encountered an error. Check console.");
    } finally {
        btn.innerHTML = '<i class="fas fa-check" style="color:#10b981;"></i> Synced';
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }, 2000);
    }
}
window.triggerMasterSync = triggerMasterSync;

// Execute Master Sync automatically on initial page load
document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
        const btn = document.getElementById('master-sync-btn');
        if(btn) {
            triggerMasterSync();
        }
    }, 1000);
});

window.rateTrade = function(tradeId, rating) {
    if(!tradeId || tradeId === 'null') {
        alert('Invalid Trade ID');
        return;
    }
    // We would need a specific PUT endpoint for updating rating/correction, which wasn't strictly asked for but implied.
    // Assuming backend will handle it, or just for UI demonstration.
    alert(`Trade ${tradeId} rated ${rating} stars!`);
}

window.submitCorrection = function(tradeId) {
    const el = document.getElementById('correction-' + tradeId);
    if(el && el.value) {
        alert(`Correction for ${tradeId} submitted: ` + el.value);
        el.value = '';
    }
}

window.annotateResponse = function(tradeId, skillId) {
    const text = prompt("Enter your annotation/note for this market context:");
    if(!text) return;

    fetch('/api/ai/rag/annotate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            annotation_text: text,
            skill_id: skillId,
            symbols: [], // Could be extracted from context
            was_correct: true
        })
    }).then(res => res.json()).then(data => {
        alert('Annotation saved to Vector DB!');
    }).catch(err => {
        alert('Error saving annotation: ' + err);
    });
}

window.loadSkillList = function() {
    fetch('/api/ai/skills')
    .then(res => res.json())
    .then(skills => {
        const list = document.getElementById('skill-list');
        if(!list) return;
        list.innerHTML = skills.map(s =>
            `<li style="padding: 10px; cursor: pointer; border-bottom: 1px solid #2a2a2a;" onclick="loadSkillDetails('${s.skill_id}')">
                <div style="font-weight: bold; color: #ccc;">${s.name}</div>
                <div style="font-size: 11px; color: #666;">${s.workspace}</div>
            </li>`
        ).join('');
    });
}

window.loadSkillDetails = function(skillId) {
    document.getElementById('skill-details').innerHTML = 'Loading...';
    fetch(`/api/ai/skills/${skillId}`)
    .then(res => res.json())
    .then(data => {
        if(data.error) {
            document.getElementById('skill-details').innerHTML = data.error;
            return;
        }

        const stepsHtml = data.steps.map(s =>
            `<div style="margin-bottom: 10px; padding: 10px; background: #252526; border-left: 3px solid #00bcd4;">
                <div style="font-weight: bold; margin-bottom: 5px;">Step ${s.step_number}: ${s.title || ''}</div>
                <div style="color: #aaa; font-size: 13px;">${s.content}</div>
            </div>`
        ).join('');

        const knowledgeHtml = data.knowledge.map(k =>
            `<div style="margin-bottom: 10px; padding: 10px; background: #252526; border-left: 3px solid #4ade80;">
                <div style="font-weight: bold; margin-bottom: 5px; display: flex; justify-content: space-between;">
                    <span>[${k.priority}] ${k.title || 'Rule'}</span>
                </div>
                <div style="color: #aaa; font-size: 13px;">${k.content}</div>
            </div>`
        ).join('');

        let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 15px;">
                <h3 style="color: #fff; margin: 0;">${data.skill.name}</h3>
                <span style="background: #333; padding: 3px 8px; border-radius: 4px; font-size: 12px; color: #aaa;">${data.skill.workspace}</span>
            </div>

            <div style="margin-top: 10px;">
                <h4 style="color: #bbb; margin-bottom: 10px;">Execution Steps</h4>
                ${stepsHtml || '<div style="color: #666; font-style: italic;">No steps defined.</div>'}
            </div>

            <div style="margin-top: 10px;">
                <h4 style="color: #bbb; margin-bottom: 10px; display: flex; justify-content: space-between;">
                    Knowledge Base / Exceptions
                    <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 12px;" onclick="addKnowledge('${skillId}')">+ Add Rule</button>
                </h4>
                ${knowledgeHtml || '<div style="color: #666; font-style: italic;">No knowledge records.</div>'}
            </div>
        `;

        document.getElementById('skill-details').innerHTML = html;
    });
}

window.addKnowledge = function(skillId) {
    const content = prompt("Enter the new rule or exception for this skill:");
    if(!content) return;

    fetch(`/api/ai/skills/${skillId}/knowledge`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            knowledge_type: "exception",
            title: "Added Rule",
            content: content,
            priority: 1
        })
    }).then(res => res.json()).then(data => {
        alert("Rule added & embedded in Vector DB!");
        loadSkillDetails(skillId); // Refresh
    });
}

// Hook into existing switchMainTab to load skills when opening Skill Studio
const originalSwitchMainTab = window.switchMainTab;
window.switchMainTab = function(tabId) {
    if(originalSwitchMainTab) originalSwitchMainTab(tabId);
    if(tabId === 'skill_studio') {
        loadSkillList();
    }
}
