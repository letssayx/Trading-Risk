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
            this.failProgress(e.message);
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
            this.failProgress(e.message);
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
            this.failProgress(e.message);
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
            this.failProgress(e.message);
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
            this.progressBar.style.backgroundColor = '#4caf50'; // Green
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
        }, 1000);
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
                color = '#4caf50'; // Green
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

                            if (item.status === 'SUCCESS') color = '#4caf50';
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
                                    let barColor = '#4caf50';
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
