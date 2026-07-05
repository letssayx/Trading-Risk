// Global function to switch tabs (moved outside class to ensure availability)
window.openImportTab = (tabName) => {
    document.querySelectorAll('.import-tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.import-tabs .tab-btn').forEach(el => el.classList.remove('active'));

    const target = document.getElementById(`tab-${tabName}`);
    if (target) {
        target.style.display = 'block';
        const btn = document.querySelector(`.import-tabs .tab-btn[data-tab="${tabName}"]`);
        if (btn) btn.classList.add('active');
    }
};

class NSEImporter {
    constructor() {
        this.modal = document.getElementById('import-view-container');
        this.progressBar = document.getElementById('progress-bar');
        this.progressText = document.getElementById('progress-text');
        this.progressArea = document.getElementById('import-progress-area');
        this.importDetails = document.getElementById('import-details');
        this.historyList = document.getElementById('import-history-list');

        // Polling state
        this.pollInterval = null;
        this.isPolling = false;

        this.initEventListeners();
        this.resumeActiveTask();
        this.initSymbolMaster();
    }

    initSymbolMaster() {
        const btnUploadCsv = document.getElementById('btn-upload-symbol-csv');
        const btnAddManual = document.getElementById('btn-add-symbol-manual');
        const btnRefresh = document.getElementById('btn-refresh-symbol-db');

        if (btnUploadCsv) {
            btnUploadCsv.addEventListener('click', async () => {
                const fileInput = document.getElementById('symbol-csv-upload');
                const file = fileInput.files[0];
                if (!file) {
                    alert('Please select a CSV file first.');
                    return;
                }

                btnUploadCsv.disabled = true;
                btnUploadCsv.textContent = 'Processing...';

                const text = await file.text();
                const lines = text.split('\n').filter(l => l.trim().length > 0);

                if (lines.length < 2) {
                    alert('CSV must contain headers and at least one row of data.');
                    btnUploadCsv.disabled = false;
                    btnUploadCsv.textContent = 'Process CSV';
                    return;
                }

                // Detect headers
                const headers = lines[0].split(',').map(h => h.trim().toLowerCase());

                const data = [];
                for (let i = 1; i < lines.length; i++) {
                    const parts = lines[i].split(',').map(p => p.trim());
                    const row = {};

                    headers.forEach((h, index) => {
                        let key = '';
                        if (h.includes('symbol')) key = 'symbol';
                        else if (h.includes('company')) key = 'company_name';
                        else if (h.includes('broad')) key = 'broad_index';
                        else if (h.includes('sector')) key = 'sector_index';
                        else if (h.includes('tier')) key = 'derivative_liquidity_tier';
                        else if (h.includes('hedge')) key = 'typical_hedge_index';

                        if (key && parts[index]) {
                            row[key] = parts[index];
                        }
                    });

                    if (row.symbol) {
                        data.push(row);
                    }
                }

                if (data.length === 0) {
                    alert('Could not parse any valid rows with a "Symbol" column.');
                    btnUploadCsv.disabled = false;
                    btnUploadCsv.textContent = 'Process CSV';
                    return;
                }

                try {
                    const response = await fetch('/api/v1/nse/symbol-master/upload', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ data: data })
                    });

                    const result = await response.json();
                    if (response.ok) {
                        alert(`Success: ${result.message}`);
                        fileInput.value = '';
                        this.refreshSymbolMasterTable();
                    } else {
                        alert(`Error: ${result.detail || result.message}`);
                    }
                } catch (e) {
                    alert(`Upload failed: ${e.message}`);
                } finally {
                    btnUploadCsv.disabled = false;
                    btnUploadCsv.textContent = 'Process CSV';
                }
            });
        }

        if (btnAddManual) {
            btnAddManual.addEventListener('click', async () => {
                const symbol = document.getElementById('sm-input-symbol').value.trim();
                if (!symbol) {
                    alert('Symbol is compulsory.');
                    return;
                }

                const row = {
                    symbol: symbol,
                    company_name: document.getElementById('sm-input-company').value.trim(),
                    broad_index: document.getElementById('sm-input-broad').value.trim(),
                    sector_index: document.getElementById('sm-input-sector').value.trim(),
                    derivative_liquidity_tier: document.getElementById('sm-input-tier').value.trim(),
                    typical_hedge_index: document.getElementById('sm-input-hedge').value.trim()
                };

                btnAddManual.disabled = true;
                btnAddManual.textContent = 'Saving...';

                try {
                    const response = await fetch('/api/v1/nse/symbol-master/upload', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ data: [row] })
                    });

                    const result = await response.json();
                    if (response.ok) {
                        // Clear inputs
                        document.querySelectorAll('[id^="sm-input-"]').forEach(el => el.value = '');
                        this.refreshSymbolMasterTable();
                    } else {
                        alert(`Error: ${result.detail || result.message}`);
                    }
                } catch (e) {
                    alert(`Save failed: ${e.message}`);
                } finally {
                    btnAddManual.disabled = false;
                    btnAddManual.textContent = 'Add / Update';
                }
            });
        }

        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.refreshSymbolMasterTable());
            // Auto load on init
            this.refreshSymbolMasterTable();
        }
    }

    async refreshSymbolMasterTable() {
        const tbody = document.getElementById('symbol-master-tbody');
        if (!tbody) return;

        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#888;">Loading...</td></tr>';

        try {
            const response = await fetch('/api/v1/nse/symbol-master');
            const result = await response.json();

            if (response.ok && result.data && result.data.length > 0) {
                tbody.innerHTML = '';
                result.data.forEach(item => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><strong>${item.symbol || '-'}</strong></td>
                        <td>${item.company_name || '-'}</td>
                        <td>${item.broad_index || '-'}</td>
                        <td>${item.sector_index || '-'}</td>
                        <td>${item.derivative_liquidity_tier || '-'}</td>
                        <td>${item.typical_hedge_index || '-'}</td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#888;">No data loaded.</td></tr>';
            }
        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#f44336;">Failed to load data: ${e.message}</td></tr>`;
        }
    }

    resumeActiveTask() {
        const activeTaskId = localStorage.getItem('activeImportTaskId');
        if (activeTaskId) {
            console.log("Resuming polling for task:", activeTaskId);
            this.progressArea.style.display = 'block';
            this.progressText.textContent = "Resuming import tracking...";
            this.pollTask(activeTaskId);
        }
    }

    initEventListeners() {
        // Latest Import
        const btnLatest = document.getElementById('btn-import-latest');
        if (btnLatest) {
            btnLatest.addEventListener('click', () => this.importLatest());
        }

        // Range Import
        const btnRange = document.getElementById('btn-import-range');
        if (btnRange) {
            btnRange.addEventListener('click', () => this.importRange());
        }

        // Manual Upload
        const btnManual = document.getElementById('btn-manual-upload');
        if (btnManual) {
            btnManual.addEventListener('click', () => this.importManual());
        }

        const manualTypeSelect = document.getElementById('manual-type');
        if (manualTypeSelect) {
            manualTypeSelect.addEventListener('change', () => {
                const hint = document.getElementById('manual-format-hint');
                const stdContainer = document.getElementById('manual-file-container');
                const divOverrideContainer = document.getElementById('manual-dividend-override-container');

                if (hint) {
                    hint.style.display = manualTypeSelect.value === 'fii_dii_cash' ? 'block' : 'none';
                }

                if (manualTypeSelect.value === 'dividend_override') {
                    if (stdContainer) stdContainer.style.display = 'none';
                    if (divOverrideContainer) divOverrideContainer.style.display = 'block';
                } else {
                    if (stdContainer) stdContainer.style.display = 'block';
                    if (divOverrideContainer) divOverrideContainer.style.display = 'none';
                }
            });
        }

        // Dividend Override Submit
        const btnDividendOverride = document.getElementById('btn-dividend-override');
        if (btnDividendOverride) {
            btnDividendOverride.addEventListener('click', () => this.submitDividendOverride());
        }

        const btnDividendOverrideDelete = document.getElementById('btn-dividend-override-delete');
        if (btnDividendOverrideDelete) {
            btnDividendOverrideDelete.addEventListener('click', () => this.deleteDividendOverride());
        }

        // Cancel Polling
        const btnCancel = document.getElementById('btn-cancel-polling');
        if (btnCancel) {
            btnCancel.addEventListener('click', async () => {
                const taskId = localStorage.getItem('activeImportTaskId');
                if (taskId) {
                    try {
                        await fetch(`/api/v1/nse/ingest/import/cancel/${taskId}`, { method: 'POST' });
                        console.log(`Sent cancel request for task ${taskId}`);
                    } catch (e) {
                        console.error("Failed to send cancel request", e);
                    }
                }
                this.stopPolling();
                if (this.progressArea) this.progressArea.style.display = 'none';
                console.log("Manually stopped tracking task.");
            });
        }

        // Pause/Resume Task
        const btnPause = document.getElementById('btn-pause-polling');
        if (btnPause) {
            btnPause.addEventListener('click', async () => {
                const taskId = localStorage.getItem('activeImportTaskId');
                if (taskId) {
                    const isPaused = btnPause.getAttribute('data-paused') === 'true';
                    const endpoint = isPaused ? 'resume' : 'pause';
                    try {
                        await fetch(`/api/v1/nse/ingest/import/${endpoint}/${taskId}`, { method: 'POST' });
                        if (isPaused) {
                            btnPause.setAttribute('data-paused', 'false');
                            btnPause.textContent = 'Pause Task';
                            btnPause.style.background = '#f39c12';
                        } else {
                            btnPause.setAttribute('data-paused', 'true');
                            btnPause.textContent = 'Resume Task';
                            btnPause.style.background = '#27ae60';
                        }
                    } catch (e) {
                        console.error(`Failed to send ${endpoint} request`, e);
                    }
                }
            });
        }

        // Force Kill Task
        const btnForceKill = document.getElementById('btn-force-kill');
        if (btnForceKill) {
            btnForceKill.addEventListener('click', async () => {
                if (!confirm("Are you sure you want to forcefully kill this task? This may leave intermediate data states.")) return;

                const taskId = localStorage.getItem('activeImportTaskId');
                if (taskId) {
                    try {
                        await fetch(`/api/v1/nse/ingest/import/force-kill/${taskId}`, { method: 'POST' });
                        console.log(`Sent force kill request for task ${taskId}`);
                    } catch (e) {
                        console.error("Failed to send force kill request", e);
                    }
                }
                this.stopPolling();
                if (this.progressArea) this.progressArea.style.display = 'none';
                console.log("Forcefully killed task and stopped tracking.");
            });
        }

        // Initial load
        this.fetchHistory();
    }

    open() {
        // Refresh history when "Import Data" main tab is opened
        this.fetchHistory();
    }

    close() {
        this.stopPolling();
    }

    async checkHealth() {
        try {
            const res = await fetch('/api/v1/nse/health/db');
            if (res.ok) {
                const data = await res.json();
                if (data.status === 'unhealthy' || data.database === 'disconnected') {
                    throw new Error(data.error || 'Database disconnected');
                }
                return true;
            }
            throw new Error(`Health Check Failed: ${res.status}`);
        } catch (e) {
            this.startProgress("Health Check Failed");
            this.failProgress(`Backend unreachable: ${e.message}`);
            return false;
        }
    }

    async importLatest() {
        if (!(await this.checkHealth())) return;

        // Collect selected patterns
        const patterns = [];
        document.querySelectorAll('.latest-type:checked').forEach(cb => {
            patterns.push(cb.value);
        });

        if (patterns.length === 0) {
            alert("Select at least one data type.");
            return;
        }

        this.startProgress("Starting latest data import...");

        try {
            const params = new URLSearchParams();
            patterns.forEach(p => params.append('patterns', p));
            const forceCheckbox = document.getElementById('force-import-latest');
            if (forceCheckbox && forceCheckbox.checked) {
                params.append('force', 'true');
            }
            const nonFoCheckbox = document.getElementById('non-fo-import-latest');
            if (nonFoCheckbox && nonFoCheckbox.checked) {
                params.append('include_non_fo', 'true');
            }
            const specificSymbol = document.getElementById('specific-symbol-latest');
            if (specificSymbol && specificSymbol.value.trim()) {
                params.append('specific_symbol', specificSymbol.value.trim().toUpperCase());
            }

            const res = await fetch(`/api/v1/nse/ingest/import/latest?${params.toString()}`, {
                method: 'POST'
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();

            // Check for task_id (new response format) or success flag (old format)
            const taskId = data.task_id || (data.success ? data.task_id : null);

            if (taskId) {
                this.pollTask(taskId);
            } else {
                this.failProgress(data.message || "Failed to start import: No Task ID");
            }
        } catch (e) {
            this.failProgress(e.message || (typeof e === 'object' ? JSON.stringify(e) : e));
        }
    }

    async importRange() {
        if (!(await this.checkHealth())) return;

        const start = document.getElementById('range-start').value;
        const end = document.getElementById('range-end').value;

        const patterns = [];
        document.querySelectorAll('.range-type:checked').forEach(cb => {
            patterns.push(cb.value);
        });

        if (!start || !end) {
            alert("Please select start and end dates.");
            return;
        }
        if (patterns.length === 0) {
            alert("Select at least one data type.");
            return;
        }

        this.startProgress(`Starting range import from ${start} to ${end}...`);

        try {
            const params = new URLSearchParams();
            params.append('start_date', start);
            params.append('end_date', end);
            patterns.forEach(p => params.append('patterns', p));
            const forceCheckbox = document.getElementById('force-import-range');
            if (forceCheckbox && forceCheckbox.checked) {
                params.append('force', 'true');
            }
            const nonFoCheckbox = document.getElementById('non-fo-import-range');
            if (nonFoCheckbox && nonFoCheckbox.checked) {
                params.append('include_non_fo', 'true');
            }
            const specificSymbol = document.getElementById('specific-symbol-range');
            if (specificSymbol && specificSymbol.value.trim()) {
                params.append('specific_symbol', specificSymbol.value.trim().toUpperCase());
            }

            const res = await fetch(`/api/v1/nse/ingest/import/range?${params.toString()}`, {
                method: 'POST'
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();

            const taskId = data.task_id || (data.success ? data.task_id : null);

            if (taskId) {
                this.pollTask(taskId);
            } else {
                this.failProgress(data.message || "Failed to start import: No Task ID");
            }
        } catch (e) {
            this.failProgress(e.message || (typeof e === 'object' ? JSON.stringify(e) : e));
        }
    }

    async submitDividendOverride() {
        if (!(await this.checkHealth())) return;

        const symbol = document.getElementById('override-symbol').value.trim().toUpperCase();
        const amount = document.getElementById('override-amount').value;
        const exDate = document.getElementById('override-ex-date').value;
        const annDate = document.getElementById('override-announcement-date').value;
        const divType = document.getElementById('override-div-type').value;

        if (!symbol || !amount || !exDate || !annDate) {
            alert("Please fill in Symbol, Amount, Ex-Date, and Announcement Date.");
            return;
        }

        const formData = new FormData();
        formData.append('symbol', symbol);
        formData.append('amount', amount);
        formData.append('ex_date', exDate);
        formData.append('announcement_date', annDate);
        formData.append('dividend_type', divType);

        this.startProgress(`Overriding Dividend for ${symbol}...`);

        try {
            const res = await fetch('/api/data/manual-override/dividend', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (!res.ok) {
                this.failProgress(typeof data.detail === 'object' ? JSON.stringify(data.detail) : (data.detail || "Override failed."));
                return;
            }

            this.successProgress(`Successfully recorded dividend for ${symbol}.`);

            // Clear inputs
            document.getElementById('override-symbol').value = '';
            document.getElementById('override-amount').value = '';
            document.getElementById('override-ex-date').value = '';
            document.getElementById('override-announcement-date').value = '';

            this.fetchHistory();
        } catch (e) {
            this.failProgress(e.message || (typeof e === 'object' ? JSON.stringify(e) : e));
        }
    }

    async deleteDividendOverride() {
        if (!(await this.checkHealth())) return;

        const symbol = document.getElementById('override-symbol').value.trim().toUpperCase();
        const amount = document.getElementById('override-amount').value;
        const annDate = document.getElementById('override-announcement-date').value;
        const divType = document.getElementById('override-div-type').value;

        if (!symbol || !amount || !annDate) {
            alert("Please fill in Symbol, Amount, and Announcement Date to delete.");
            return;
        }

        if (!confirm(`Are you sure you want to delete the dividend override for ${symbol} with amount ${amount}?`)) {
            return;
        }

        const formData = new FormData();
        formData.append('symbol', symbol);
        formData.append('amount', amount);
        formData.append('announcement_date', annDate);
        formData.append('dividend_type', divType);

        this.startProgress(`Deleting Dividend Override for ${symbol}...`);

        try {
            const res = await fetch('/api/data/manual-override/dividend', {
                method: 'DELETE',
                body: formData
            });

            const data = await res.json();
            if (!res.ok || !data.success) {
                this.failProgress(typeof data.detail === 'object' ? JSON.stringify(data.detail) : (data.detail || data.message || "Delete failed."));
                return;
            }

            this.successProgress(`Successfully deleted dividend override for ${symbol}.`);

            // Clear inputs
            document.getElementById('override-symbol').value = '';
            document.getElementById('override-amount').value = '';
            document.getElementById('override-ex-date').value = '';
            document.getElementById('override-announcement-date').value = '';

            this.fetchHistory();
        } catch (e) {
            this.failProgress(e.message || (typeof e === 'object' ? JSON.stringify(e) : e));
        }
    }

    async importManual() {
        if (!(await this.checkHealth())) return;

        const fileInput = document.getElementById('manual-file');
        const fileType = document.getElementById('manual-type').value;
        const fileDate = document.getElementById('manual-date') ? document.getElementById('manual-date').value : null;

        if (!fileInput.files || fileInput.files.length === 0) {
            alert("Please select a file.");
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("file_type", fileType);
        if (fileDate) formData.append("file_date", fileDate);

        this.startProgress(`Uploading ${file.name} as ${fileType}...`);

        try {
            const res = await fetch('/api/data/upload/generic', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();

            if (data.success) {
                this.successProgress(`Successfully imported ${data.rows_processed} rows for ${data.date}`);
                this.renderDetails({[data.type]: {status: 'SUCCESS', rows_processed: data.rows_processed}});
            } else {
                this.failProgress("Import reported failure without error message");
            }

        } catch (e) {
            this.failProgress(e.message || (typeof e === 'object' ? JSON.stringify(e) : e));
        }
    }

    async retryImport(dateStr, pattern) {
        if (!(await this.checkHealth())) return;

        this.startProgress(`Retrying import for ${pattern} on ${dateStr}...`);

        try {
            const params = new URLSearchParams();
            params.append('start_date', dateStr);
            params.append('end_date', dateStr);
            params.append('patterns', pattern);
            params.append('force', 'true');

            const res = await fetch(`/api/v1/nse/ingest/import/range?${params.toString()}`, {
                method: 'POST'
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();
            const taskId = data.task_id || (data.success ? data.task_id : null);

            if (taskId) {
                this.pollTask(taskId);
            } else {
                this.failProgress(data.message || "Failed to start retry task: No Task ID");
            }
        } catch (e) {
            this.failProgress(e.message || (typeof e === 'object' ? JSON.stringify(e) : e));
        }
    }

    openAuditLog(dateStr, level = 'ERROR') {
        const auditStart = document.getElementById('audit-start');
        const auditEnd = document.getElementById('audit-end');
        const auditLevel = document.getElementById('audit-level');

        if (auditStart) auditStart.value = dateStr;
        if (auditEnd) auditEnd.value = dateStr;
        if (auditLevel) auditLevel.value = level;

        if (window.switchMainTab) {
            window.switchMainTab('audit');
        }
    }

    // --- UI Helpers ---

    startProgress(msg) {
        if (this.progressArea) this.progressArea.style.display = 'block';
        if (this.progressText) this.progressText.textContent = msg;
        if (this.progressBar) {
            this.progressBar.style.width = '5%';
            this.progressBar.style.backgroundColor = '#00bcd4'; // Cyan
            this.progressBar.parentElement.style.display = 'block';
        }
        if (this.importDetails) this.importDetails.innerHTML = '';
    }

    updateProgress(percent, msg, detailsHTML) {
        if (this.progressBar) this.progressBar.style.width = `${percent}%`;
        if (msg && this.progressText) this.progressText.textContent = msg;
        if (detailsHTML && this.importDetails) this.importDetails.innerHTML = detailsHTML;
    }

    failProgress(error) {
        if (this.progressBar) this.progressBar.style.backgroundColor = '#f44336'; // Red
        if (this.progressText) this.progressText.textContent = `Error: ${error}`;
        this.stopPolling();
    }

    successProgress(msg) {
        if (this.progressBar) {
            this.progressBar.style.width = '100%';
            this.progressBar.style.backgroundColor = '#3176B8'; // Green
        }
        if (this.progressText) this.progressText.textContent = msg || "Import Completed Successfully";
        this.fetchHistory();
        this.stopPolling();
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
        this.isPolling = false;
        localStorage.removeItem('activeImportTaskId');
    }

    pollTask(taskId) {
        if (this.isPolling) this.stopPolling();
        this.isPolling = true;

        localStorage.setItem('activeImportTaskId', taskId);
        this.pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/v1/nse/ingest/import/status/${taskId}`);
                if (!res.ok) throw new Error("Status check failed");

                const data = await res.json();

                // Handle Celery State or Custom Status
                const state = data.state || data.status;

                if (state === 'SUCCESS') {
                    this.successProgress("Import Completed!");
                    // If result details available in result (Celery) or direct response
                    const result = data.result || data;
                    if (result && result.details) {
                        this.renderDetails(result.details);
                    }
                } else if (state === 'FAILURE') {
                    this.failProgress(data.error || "Import task failed");
                } else {
                    // PROGRESS or PENDING
                    let percent = 5;
                    let msg = "Queued...";

                    if (state === 'PROGRESS' && data.meta) {
                        percent = data.meta.percent || data.meta.progress || 5;
                        msg = `Processing: ${data.meta.current_file || data.meta.current_date || '...'}`;

                        if (data.meta.files_completed) {
                             msg += ` (${data.meta.files_completed.length} files done)`;
                        }
                    }

                    this.updateProgress(percent, msg);
                }
            } catch (e) {
                console.error("Polling error", e);
                // Don't stop polling immediately on network blip
            }
        }, 5000); // Polling every 5 seconds to reduce DB contention
    }

    renderDetails(details) {
        if (!details || !this.importDetails) return;

        let html = '<div style="margin-top:10px; border-top:1px solid #444; padding-top:10px;">';

        // details is object { pattern: { status: 'SUCCESS', ... } }
        Object.entries(details).forEach(([key, res]) => {
            let color = '#f44336'; // Default red for failure
            let icon = '✗';
            let info = res.error || 'Unknown error';

            if (res.status === 'SUCCESS') {
                color = '#3176B8'; // Green
                icon = '✓';
                info = `${res.rows_processed} rows`;
            } else if (res.status === 'EMPTY' || res.status === 'SKIPPED') {
                color = '#ff9800'; // Orange/Yellow
                icon = '⚠';
                info = res.status === 'EMPTY' ? 'No records found' : (res.reason || 'Skipped');
            }

            html += `<div style="color:${color}; margin-bottom:4px; font-size:0.9em;">
                ${icon} <strong>${key}</strong>: ${info}
            </div>`;
        });

        html += '</div>';
        this.importDetails.innerHTML = html;
    }

    async fetchHistory() {
        if (!this.historyList) {
            console.warn("History list element not found, cannot render.");
            return;
        }

        try {
            console.log("Fetching history...");
            const res = await fetch('/api/v1/nse/ingest/stats');
            if (res.ok) {
                const data = await res.json(); // { summary: [...], period: {...} }
                console.log("History data received:", data);

                if (data.summary && data.summary.length > 0) {
                    // Group by table_name to avoid duplicates
                    const grouped = {};
                    data.summary.forEach(item => {
                        if (!grouped[item.table_name]) grouped[item.table_name] = [];
                        grouped[item.table_name].push(item);
                    });

                    // Render as Table
                    let html = '<table class="data-table" style="margin-top:10px; width:100%;"><thead><tr><th>Table Name</th><th>Status Summary</th><th>Last Data Date</th><th>Downloaded At</th></tr></thead><tbody>';

                    Object.keys(grouped).sort().forEach(table => {
                        const items = grouped[table];
                        // Create badges for each status
                        const badges = items.map(item => {
                            let color = '#d4d4d4';

                            if (item.status === 'SUCCESS') color = '#3176B8';
                            else if (item.status === 'FAILED' || item.status === 'ERROR') color = '#f44336';
                            else if (item.status === 'EMPTY' || item.status === 'SKIPPED') color = '#ff9800';

                            let extraActions = '';
                            if (item.status === 'FAILED' || item.status === 'ERROR') {
                                // We don't have the exact date of the failed run per-item in this grouped view,
                                // but we do have last_import_date. If we want precision, we use the max date.
                                const dateArg = item.last_import_date ? `'${item.last_import_date}'` : "''";
                                const patternArg = `'${table}'`;
                                extraActions = `
                                    <button class="btn btn-primary" style="padding: 2px 5px; font-size: 0.7em; margin-left: 5px;" onclick="window.uploader.retryImport(${dateArg}, ${patternArg})">Retry</button>
                                    <button class="btn btn-secondary" style="padding: 2px 5px; font-size: 0.7em; margin-left: 5px;" onclick="window.uploader.openAuditLog(${dateArg})">View Log</button>
                                `;
                            }

                            return `<div style="margin-bottom:2px; display: flex; align-items: center;">
                                <span style="font-size:0.85em; color:${color}; font-weight:500; margin-right:8px;">
                                    ${item.status}: ${item.job_count}
                                </span>
                                ${extraActions}
                            </div>`;
                        }).join('');

                        // Find max dates (using the aggregate logic from backend, or item iteration if needed)
                        let lastDataDate = '';
                        let lastDownloadTime = '';

                        items.forEach(item => {
                            if (item.last_import_date && (!lastDataDate || item.last_import_date > lastDataDate)) {
                                lastDataDate = item.last_import_date;
                            }
                            if (item.last_download_time && (!lastDownloadTime || item.last_download_time > lastDownloadTime)) {
                                lastDownloadTime = item.last_download_time;
                            }
                        });

                        // Format timestamps
                        const fmtDate = lastDataDate ? lastDataDate : '-';
                        let fmtTime = '-';
                        if (lastDownloadTime) {
                            try {
                                fmtTime = new Date(lastDownloadTime).toLocaleString();
                            } catch (e) {
                                fmtTime = lastDownloadTime;
                            }
                        }

                        // Show time bar for visual recency indicator
                        let timeBar = '';
                        if (lastDownloadTime) {
                            try {
                                const now = new Date();
                                const dlTime = new Date(lastDownloadTime);
                                if (!isNaN(dlTime.getTime())) { // Check if valid date
                                    const diffHours = (now - dlTime) / (1000 * 60 * 60);
                                    let barColor = '#3176B8';
                                    let barWidth = '100%';

                                    // Decay bar based on age (e.g. 24h)
                                    // Ensure difference is positive just in case of timezone mismatches
                                    const safeDiffHours = Math.max(0, diffHours);
                                    if (safeDiffHours < 24) {
                                        barWidth = `${Math.max(10, 100 - (safeDiffHours * 4))}%`;
                                    } else {
                                        barWidth = '10%';
                                        barColor = '#888';
                                    }
                                    timeBar = `<div style="width:100%; height:4px; background:#333; margin-top:4px; border-radius:2px; overflow:hidden; position:relative; min-width:100px;">
                                        <div style="width:${barWidth}; height:100%; background:${barColor}; border-radius:2px;"></div>
                                    </div>`;
                                }
                            } catch (e) {
                                console.warn("Time bar error:", e);
                            }
                        }


                        html += `
                            <tr>
                                <td style="color:#00bcd4; font-weight:500; vertical-align:top; min-width:120px;">
                                    <div style="margin-bottom: 2px;">${table}</div>
                                    ${timeBar}
                                </td>
                                <td>${badges}</td>
                                <td>${fmtDate}</td>
                                <td style="font-size:0.85em; color:#aaa;">${fmtTime}</td>
                            </tr>
                        `;
                    });
                    html += '</tbody></table>';
                    this.historyList.innerHTML = html;
                } else {
                    console.log("Summary empty");
                    this.historyList.innerHTML = '<p style="color:#888;">No recent imports found.</p>';
                }
            } else {
                console.error("Stats API failed", res.status);
                this.historyList.innerHTML = '<p style="color:#f44336">Failed to load history</p>';
            }
        } catch (e) {
            console.error("Failed to fetch history", e);
            this.historyList.innerHTML = '<p style="color:#f44336">History unavailable: ' + e.message + '</p>';
        }
    }
}

// Global instance for HTML onclick bindings
// Using window.uploader to match workbench.html expectations
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.uploader = new NSEImporter();
    } catch (e) {
        console.error("Failed to init NSEImporter:", e);
    }
});
