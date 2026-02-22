/**
 * NSE Importer - Supports Latest, Range, and Manual Imports
 */
class NSEImporter {
    constructor() {
        this.modal = document.getElementById('bhavcopy-upload-modal');
        this.progressBar = document.getElementById('progress-bar');
        this.progressText = document.getElementById('progress-text');
        this.progressArea = document.getElementById('import-progress-area');
        this.importDetails = document.getElementById('import-details');

        // Manual Upload Elements
        this.fileInput = document.getElementById('bhavcopy-file');
        this.confirmBtn = document.getElementById('confirm-import-btn');

        this.initEventListeners();
    }

    initEventListeners() {
        // Tab Switching
        window.openImportTab = (tabName) => {
            document.querySelectorAll('.import-tab-content').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.import-tabs .tab-btn').forEach(el => el.classList.remove('active'));

            document.getElementById(`tab-${tabName}`).style.display = 'block';
            document.querySelector(`.tab-btn[data-tab="${tabName}"]`).classList.add('active');
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

        // Manual Upload (Legacy)
        if (this.fileInput) {
            this.fileInput.addEventListener('change', () => {
                this.confirmBtn.disabled = !this.fileInput.files.length;
            });
        }
        if (this.confirmBtn) {
            this.confirmBtn.addEventListener('click', () => this.importManual());
        }

        // Close logic
        const closeSpan = document.querySelector('.close');
        if (closeSpan) {
            closeSpan.addEventListener('click', () => this.close());
        }
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) this.close();
        });
    }

    open() {
        if(this.modal) {
            this.modal.style.display = 'flex';
            this.fetchHistory();
        }
    }

    close() {
        if(this.modal) this.modal.style.display = 'none';
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

        const patterns = Array.from(document.querySelectorAll('.latest-type:checked')).map(cb => cb.value);
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
                throw new Error(errData.detail?.message || errData.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();

            if (data.success) {
                this.pollTask(data.task_id);
            } else {
                this.failProgress(data.message || "Failed to start import");
            }
        } catch (e) {
            this.failProgress(e.message);
        }
    }

    async importRange() {
        if (!(await this.checkHealth())) return;

        const start = document.getElementById('range-start').value;
        const end = document.getElementById('range-end').value;
        const patterns = Array.from(document.querySelectorAll('.range-type:checked')).map(cb => cb.value);

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
                throw new Error(errData.detail?.message || errData.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();

            if (data.success) {
                this.pollTask(data.task_id);
            } else {
                this.failProgress(data.message || "Failed to start import");
            }
        } catch (e) {
            this.failProgress(e.message);
        }
    }

    async importManual() {
        // Legacy Support for Manual Upload
        alert("Manual upload is using legacy endpoint. Please use 'Latest' or 'Range' for best results.");
    }

    // --- UI Helpers ---

    startProgress(msg) {
        this.progressArea.style.display = 'block';
        this.progressText.textContent = msg;
        this.progressBar.style.width = '10%';
        this.progressBar.style.backgroundColor = '#00bcd4';
        this.importDetails.textContent = '';
    }

    updateProgress(percent, msg) {
        this.progressBar.style.width = `${percent}%`;
        if (msg) this.progressText.textContent = msg;
    }

    failProgress(error) {
        this.progressBar.style.backgroundColor = '#f44336';
        this.progressText.textContent = `Error: ${error}`;
        // Keep error visible
    }

    successProgress(msg) {
        this.progressBar.style.width = '100%';
        this.progressBar.style.backgroundColor = '#4caf50';
        this.progressText.textContent = msg || "Import Completed Successfully";
        this.fetchHistory(); // Refresh history

        // Trigger UI refresh if needed
        if (typeof Edge !== 'undefined' && Edge.fetchContext) {
            Edge.fetchContext();
        }
    }

    pollTask(taskId) {
        // Placeholder for real polling
        let progress = 10;
        const interval = setInterval(() => {
            progress += 5;
            if (progress > 90) progress = 90;
            this.updateProgress(progress, "Processing... (Check logs for details)");
        }, 500);

        setTimeout(() => {
            clearInterval(interval);
            this.successProgress("Import task submitted (Background processing)");
        }, 3000);
    }

    async fetchHistory() {
        const list = document.getElementById('import-history-list');
        if (!list) return;

        try {
            const res = await fetch('/api/v1/nse/ingest/stats');
            if (res.ok) {
                const data = await res.json(); // ImportStatsResponse

                if (data.summary && data.summary.length > 0) {
                    let html = '<ul style="list-style:none; padding:0;">';
                    data.summary.forEach(item => {
                        html += `
                            <li style="margin-bottom:5px; padding:5px; background:#333; border-radius:3px; display:flex; justify-content:space-between;">
                                <span>${item.table_name}</span>
                                <span>${item.status} (${item.job_count})</span>
                            </li>
                        `;
                    });
                    html += '</ul>';
                    list.innerHTML = html;
                } else {
                    list.innerHTML = '<p>No recent imports found.</p>';
                }
            } else {
                list.innerHTML = '<p style="color:#f44336">Failed to load history (DB offline?)</p>';
            }
        } catch (e) {
            console.error("Failed to fetch history", e);
            list.innerHTML = '<p style="color:#f44336">History unavailable</p>';
        }
    }
}

const uploader = new NSEImporter();
