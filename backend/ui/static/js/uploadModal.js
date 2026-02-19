/**
 * Enhanced Bhavcopy Uploader with Split CM/FO support
 */
class BhavcopyUploader {
    constructor() {
        this.modal = document.getElementById('bhavcopy-upload-modal');

        // Inputs
        this.fileInputCM = document.getElementById('bhavcopy-file-cm');
        this.fileInputFO = document.getElementById('bhavcopy-file-fo');

        // Buttons
        this.btnPreviewCM = document.getElementById('btn-preview-cm');
        this.btnPreviewFO = document.getElementById('btn-preview-fo');
        this.confirmBtn = document.getElementById('confirm-import-btn');
        this.cancelBtn = document.getElementById('cancel-import-btn');

        // Status & Preview
        this.statusCM = document.getElementById('status-cm');
        this.statusFO = document.getElementById('status-fo');
        this.statusGlobal = document.getElementById('global-status');
        this.previewDiv = document.getElementById('upload-preview');
        this.overwriteCheckbox = document.getElementById('overwrite-existing');

        // State
        this.preparedImports = {
            CM: null, // { file, date, count }
            FO: null
        };

        this.initEventListeners();
    }

    initEventListeners() {
        if (this.btnPreviewCM) this.btnPreviewCM.addEventListener('click', () => this.handlePreview('CM'));
        if (this.btnPreviewFO) this.btnPreviewFO.addEventListener('click', () => this.handlePreview('FO'));

        if (this.confirmBtn) this.confirmBtn.addEventListener('click', () => this.confirmImport());
        if (this.cancelBtn) this.cancelBtn.addEventListener('click', () => this.close());

        // Close on outside click
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        // Close on X
        const closeSpan = this.modal ? this.modal.querySelector('.close') : null;
        if (closeSpan) {
            closeSpan.addEventListener('click', () => this.close());
        }
    }

    open() {
        if(this.modal) this.modal.style.display = 'flex';
        this.reset();
    }

    close() {
        if(this.modal) this.modal.style.display = 'none';
    }

    async triggerBulkImport() {
        const pathInput = document.getElementById('bulk-folder-path');
        const status = document.getElementById('bulk-status');
        const path = pathInput ? pathInput.value : '';

        if (!path) {
            alert("Please enter a folder path.");
            return;
        }

        status.style.display = 'block';
        status.innerHTML = "Starting Bulk Import... (Check Server Logs)";
        status.className = "status-message info";

        try {
            // We need a backend endpoint for this.
            // Assuming we added /api/data/upload/bulk in routes.
            const res = await fetch('/api/data/upload/bulk', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ folder_path: path })
            });
            const data = await res.json();

            if (data.success) {
                status.innerHTML = `Import Complete. Processed: ${data.processed}, Errors: ${data.errors}`;
                status.className = "status-message success";
            } else {
                status.innerHTML = "Error: " + data.message;
                status.className = "status-message error";
            }
        } catch (e) {
            status.innerHTML = "Error: " + e.message;
            status.className = "status-message error";
        }
    }

    reset() {
        if(this.fileInputCM) this.fileInputCM.value = '';
        if(this.fileInputFO) this.fileInputFO.value = '';
        if(this.statusCM) this.statusCM.innerHTML = '';
        if(this.statusFO) this.statusFO.innerHTML = '';
        if(this.statusGlobal) this.statusGlobal.innerHTML = '';
        if(this.previewDiv) this.previewDiv.innerHTML = '<p class="placeholder">Select a file and click Preview to verify data.</p>';
        this.preparedImports = { CM: null, FO: null };
        this.updateConfirmButton();
    }

    showStatus(msg, type, targetId) {
        const el = document.getElementById(targetId);
        if (!el) return;
        el.innerHTML = msg;
        el.className = 'status-message ' + type;
    }

    async handlePreview(segment) {
        const fileInput = segment === 'CM' ? this.fileInputCM : this.fileInputFO;
        const statusId = segment === 'CM' ? 'status-cm' : 'status-fo';

        const file = fileInput.files[0];
        if (!file) {
            this.showStatus('Please select a file first.', 'error', statusId);
            return;
        }

        this.showStatus('Analyzing...', 'info', statusId);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/data/upload/bhavcopy/preview', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // Check if the requested segment exists in the file
                const segStats = data.stats[segment];
                if (!segStats || segStats.total_rows === 0) {
                     this.showStatus(`⚠️ No ${segment} data found in this file.`, 'warning', statusId);
                     return;
                }

                this.preparedImports[segment] = {
                    file: file,
                    date: data.file_date,
                    count: segStats.total_rows,
                    preview: data.preview[segment]
                };

                this.showStatus(`✅ Ready: ${segStats.total_rows} rows (${data.file_date})`, 'success', statusId);

                // Show unified preview
                this.renderPreview();
                this.updateConfirmButton();

            } else {
                this.showStatus('Error: ' + data.detail, 'error', statusId);
            }
        } catch (error) {
            this.showStatus('Error: ' + error.message, 'error', statusId);
        }
    }

    renderPreview() {
        let html = '';

        if (this.preparedImports.CM) {
            html += this.renderSegmentTable('CM', this.preparedImports.CM);
        }

        if (this.preparedImports.FO) {
            html += this.renderSegmentTable('FO', this.preparedImports.FO);
        }

        if (!html) html = '<p class="placeholder">Select a file and click Preview to verify data.</p>';

        this.previewDiv.innerHTML = html;
    }

    renderSegmentTable(segment, data) {
        let html = `<h4>${segment} Preview (${data.date})</h4>`;
        html += `<div style="overflow-x:auto; margin-bottom:20px;"><table class="preview-table" style="width:100%;">`;
        html += `<thead><tr>`;

        if (segment === 'CM') {
            html += `<th>Symbol</th><th>Series</th><th>Close</th><th>Volume</th>`;
        } else {
            html += `<th>Symbol</th><th>Type</th><th>Expiry</th><th>Strike</th><th>Opt</th><th>Close</th><th>OI</th>`;
        }
        html += `</tr></thead><tbody>`;

        data.preview.forEach(row => {
            html += `<tr>`;
            if (segment === 'CM') {
                html += `<td>${row.symbol}</td><td>${row.series}</td><td>${row.close}</td><td>${row.volume}</td>`;
            } else {
                html += `<td>${row.symbol}</td><td>${row.instrument_type}</td><td>${row.expiry}</td><td>${row.strike}</td><td>${row.option_type}</td><td>${row.close}</td><td>${row.open_interest}</td>`;
            }
            html += `</tr>`;
        });

        html += `</tbody></table></div>`;
        return html;
    }

    updateConfirmButton() {
        const hasData = this.preparedImports.CM || this.preparedImports.FO;
        this.confirmBtn.disabled = !hasData;
        this.confirmBtn.innerHTML = hasData ? 'Import Selected' : 'Import Selected';
    }

    async confirmImport() {
        const tasks = [];
        const overwrite = this.overwriteCheckbox.checked;
        this.confirmBtn.disabled = true;
        this.showStatus('Starting import...', 'info', 'global-status');

        if (this.preparedImports.CM) {
            tasks.push(this.uploadSegment('CM', this.preparedImports.CM, overwrite));
        }
        if (this.preparedImports.FO) {
            tasks.push(this.uploadSegment('FO', this.preparedImports.FO, overwrite));
        }

        try {
            const results = await Promise.all(tasks);
            const success = results.every(r => r.success);

            if (success) {
                const total = results.reduce((sum, r) => sum + r.inserted, 0);
                this.showStatus(`✅ Import Complete! Total ${total} rows inserted.`, 'success', 'global-status');
                // Optional: Clear inputs?
                // this.reset();
            } else {
                this.showStatus('⚠️ Some imports failed. Check console.', 'warning', 'global-status');
            }
        } catch (e) {
            this.showStatus('Error: ' + e.message, 'error', 'global-status');
        } finally {
            this.confirmBtn.disabled = false;
        }
    }

    async uploadSegment(segment, importData, overwrite) {
        const formData = new FormData();
        formData.append('file', importData.file);
        formData.append('file_date', importData.date);
        formData.append('overwrite_existing', overwrite);
        formData.append('segments', JSON.stringify([segment]));

        const res = await fetch('/api/data/upload/bhavcopy/import', {
            method: 'POST',
            body: formData
        });
        return await res.json();
    }
}

const uploader = new BhavcopyUploader();
