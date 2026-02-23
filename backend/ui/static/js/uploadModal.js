class NSEImporter {
    constructor() {
        this.modal = document.getElementById('bhavcopy-upload-modal');
        this.progressBar = document.getElementById('import-progress-bar');
        this.progressText = document.getElementById('import-progress-text');
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

            const target = document.getElementById(tabName);
            if (target) {
                target.style.display = 'block';
                const btn = document.querySelector(`.tab-btn[onclick="openImportTab('${tabName}')"]`);
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
        const closeSpan = document.querySelector('.close-modal');
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
            // Send as JSON body or query params?
            // Existing backend expects list of strings in body or query?
            // Let's use query params for simplicity as per previous code
            const params = new URLSearchParams();
            patterns.forEach(p => params.append('patterns', p));

            const res = await fetch(`/api/v1/nse/import/latest?${params.toString()}`, {
                method: 'POST'
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();

            if (data.task_id) {
                this.pollTask(data.task_id);
            } else {
                this.failProgress("Failed to start import: No Task ID returned");
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

            const res = await fetch(`/api/v1/nse/import/range?${params.toString()}`, {
                method: 'POST'
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();

            if (data.task_id) {
                this.pollTask(data.task_id);
            } else {
                this.failProgress("Failed to start import: No Task ID returned");
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
            this.progressBar.style.backgroundColor = '#2196F3'; // Blue
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
                const res = await fetch(`/api/v1/nse/import/status/${taskId}`);
                if (!res.ok) throw new Error("Status check failed");

                const data = await res.json();

                if (data.state === 'SUCCESS') {
                    this.successProgress("Import Completed!");
                    // If result details available in result
                    if (data.result && data.result.details) {
                        this.renderDetails(data.result.details);
                    }
                } else if (data.state === 'FAILURE') {
                    this.failProgress(data.error || "Import task failed");
                } else {
                    // PROGRESS or PENDING
                    let percent = 5;
                    let msg = "Queued...";

                    if (data.state === 'PROGRESS' && data.meta) {
                        percent = data.meta.percent || data.meta.progress || 5;
                        msg = `Processing: ${data.meta.current_file || data.meta.current_date || '...'}`;

                        // Render interim details if available
                        // Only for range import maybe? Or if we have completed files list
                        if (data.meta.files_completed) {
                             // Simplified status update
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

            html += `<div style="color:${color}; margin-bottom:4px;">
                ${icon} <strong>${key}</strong>: ${info}
            </div>`;
        });

        html += '</div>';
        this.importDetails.innerHTML = html;
    }

    async fetchHistory() {
        if (!this.historyList) return;

        try {
            // Endpoint to get recent import logs
            // We might need to add this endpoint or query stats
            // Let's assume /stats endpoint returns summary
            // But wait, get_import_stats returns dict not list of logs?
            // It returns { "summary": [ {table, status, count} ] }

            // Just clearing for now as we don't have a dedicated history endpoint returning list of jobs
            // We can implement one if needed, but 'stats' gives aggregated view.

            // Placeholder
            this.historyList.innerHTML = '<p style="color:#888; font-style:italic;">History updated on refresh</p>';

        } catch (e) {
            console.error("Failed to fetch history", e);
        }
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    window.nseImporter = new NSEImporter();
});
