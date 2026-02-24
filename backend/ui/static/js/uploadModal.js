class NSEImporter {
    constructor() {
        this.modal = document.getElementById('bhavcopy-upload-modal');
        this.progressBar = document.getElementById('progress-bar');
        this.progressText = document.getElementById('progress-text');
        this.progressArea = document.getElementById('import-progress-area');
        this.importDetails = document.getElementById('import-details');
        this.historyList = document.getElementById('import-history-list');

        // Polling state
        this.pollInterval = null;
        this.isPolling = false;

        this.initEventListeners();
    }

    initEventListeners() {
        // Tab Switching
        window.openImportTab = (tabName) => {
            document.querySelectorAll('.import-tab-content').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

            const target = document.getElementById(`tab-${tabName}`);
            if (target) {
                target.style.display = 'block';
                const btn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
                if (btn) btn.classList.add('active');
            }
        };

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

        // Close logic
        const closeSpan = document.querySelector('.close');
        if (closeSpan) {
            closeSpan.addEventListener('click', () => this.close());
        }
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) this.close();
        });

        // Initial load
        this.fetchHistory();
    }

    open() {
        if(this.modal) {
            this.modal.style.display = 'flex';
            this.fetchHistory();
        } else {
            console.error("NSE Import Modal not found in DOM");
        }
    }

    close() {
        if(this.modal) this.modal.style.display = 'none';
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
    }

    pollTask(taskId) {
        if (this.isPolling) this.stopPolling();
        this.isPolling = true;

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
            const color = res.status === 'SUCCESS' ? '#4caf50' : '#f44336';
            const icon = res.status === 'SUCCESS' ? '✓' : '✗';
            const info = res.status === 'SUCCESS' ? `${res.rows_processed} rows` : res.error;

            html += `<div style="color:${color}; margin-bottom:4px; font-size:0.9em;">
                ${icon} <strong>${key}</strong>: ${info}
            </div>`;
        });

        html += '</div>';
        this.importDetails.innerHTML = html;
    }

    async fetchHistory() {
        if (!this.historyList) return;

        try {
            const res = await fetch('/api/v1/nse/ingest/stats');
            if (res.ok) {
                const data = await res.json(); // { summary: [...], period: {...} }

                if (data.summary && data.summary.length > 0) {
                    let html = '<ul style="list-style:none; padding:0;">';
                    data.summary.forEach(item => {
                        const color = item.status === 'SUCCESS' ? '#4caf50' : (item.status === 'FAILED' ? '#f44336' : '#aaa');
                        html += `
                            <li style="margin-bottom:5px; padding:5px; background:#333; border-radius:3px; display:flex; justify-content:space-between; align-items:center;">
                                <span>${item.table_name}</span>
                                <span style="font-size:0.8em; color:${color}; border:1px solid ${color}; padding:2px 6px; border-radius:3px;">
                                    ${item.status} (${item.job_count})
                                </span>
                            </li>
                        `;
                    });
                    html += '</ul>';
                    this.historyList.innerHTML = html;
                } else {
                    this.historyList.innerHTML = '<p style="color:#888;">No recent imports found.</p>';
                }
            } else {
                this.historyList.innerHTML = '<p style="color:#f44336">Failed to load history</p>';
            }
        } catch (e) {
            console.error("Failed to fetch history", e);
            this.historyList.innerHTML = '<p style="color:#f44336">History unavailable</p>';
        }
    }
}

// Global instance for HTML onclick bindings
// Using window.uploader to match workbench.html expectations
document.addEventListener('DOMContentLoaded', () => {
    window.uploader = new NSEImporter();
});
