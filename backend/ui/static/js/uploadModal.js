/**
 * Enhanced Bhavcopy Uploader with F&O support
 */
class BhavcopyUploader {
    constructor() {
        this.modal = document.getElementById('bhavcopy-upload-modal');
        this.fileInput = document.getElementById('bhavcopy-file');
        this.previewDiv = document.getElementById('upload-preview');
        this.statusDiv = document.getElementById('upload-status');
        this.confirmBtn = document.getElementById('confirm-import-btn');
        this.cancelBtn = document.getElementById('cancel-import-btn');
        this.overwriteCheckbox = document.getElementById('overwrite-existing');
        this.segmentCheckboxes = {
            cm: document.getElementById('import-segment-cm'),
            fo: document.getElementById('import-segment-fo')
        };

        this.selectedFile = null;
        this.previewData = null;

        this.initEventListeners();
    }

    initEventListeners() {
        // Import Type Switch
        const radios = document.querySelectorAll('input[name="import-type"]');
        radios.forEach(r => {
            r.addEventListener('change', (e) => {
                const hint = document.getElementById('file-hint');
                if (e.target.value === 'historical') {
                    hint.textContent = 'Upload Annual/Monthly ZIP (Any UDIFF compatible)';
                } else {
                    hint.textContent = 'Expected format: BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip';
                }
            });
        });

        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }
        if (this.confirmBtn) {
            this.confirmBtn.addEventListener('click', () => this.confirmImport());
        }
        if (this.cancelBtn) {
            this.cancelBtn.addEventListener('click', () => this.close());
        }

        // Close on outside click
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        // Close on X
        const closeSpan = document.querySelector('.close');
        if (closeSpan) {
            closeSpan.addEventListener('click', () => this.close());
        }
    }

    open() {
        if(this.modal) this.modal.style.display = 'flex';
        if(this.previewDiv) this.previewDiv.innerHTML = '<p class="placeholder">Select a file to see preview</p>';
        if(this.fileInput) this.fileInput.value = '';
        if(this.statusDiv) this.statusDiv.innerHTML = '';
        this.previewData = null;
        this.selectedFile = null;
        if(this.confirmBtn) this.confirmBtn.disabled = true;
    }

    close() {
        if(this.modal) this.modal.style.display = 'none';
    }

    showStatus(msg, type) {
        if (!this.statusDiv) return;
        this.statusDiv.innerHTML = msg;
        this.statusDiv.className = 'status-message ' + type;
    }

    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        this.selectedFile = file;
        this.showStatus('Processing file...', 'info');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/data/upload/bhavcopy/preview', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.previewData = data;
                this.showPreview(data);

                // Enable confirm button only after preview
                this.confirmBtn.disabled = false;

                // Show warning if data exists
                if (data.warnings.date_exists) {
                    this.showStatus(
                        `⚠️ Data for ${data.file_date} already exists in database. ` +
                        'Check "Overwrite" to replace it.',
                        'warning'
                    );
                    this.overwriteCheckbox.parentElement.parentElement.style.display = 'block';
                } else {
                    this.overwriteCheckbox.parentElement.parentElement.style.display = 'none';
                }

                // Show if file was imported before
                if (data.warnings.already_imported) {
                    this.showStatus(
                        `ℹ️ This file was previously imported on ${data.warnings.previous_import_date}`,
                        'info'
                    );
                }

            } else {
                this.showStatus('Error: ' + data.detail, 'error');
            }
        } catch (error) {
            this.showStatus('Error uploading file: ' + error.message, 'error');
        }
    }

    showPreview(data) {
        let html = `
            <div class="preview-stats">
                <p><strong>File:</strong> ${data.filename}</p>
                <p><strong>Date:</strong> ${data.file_date}</p>
                <p><strong>Total rows:</strong> ${data.total_rows}</p>
            </div>

            <div class="segment-tabs">
                <button class="tab-btn active" data-segment="CM">Cash (CM)</button>
                <button class="tab-btn" data-segment="FO">F&O (Derivatives)</button>
            </div>
        `;

        // CM Preview
        html += `<div id="preview-CM" class="segment-preview active">`;
        html += this.renderSegmentPreview('Cash', data.stats.CM, data.preview.CM);
        html += `</div>`;

        // FO Preview
        html += `<div id="preview-FO" class="segment-preview">`;
        html += this.renderSegmentPreview('F&O', data.stats.FO, data.preview.FO);
        html += `</div>`;

        this.previewDiv.innerHTML = html;

        // Add tab switching
        const self = this; // Capture this
        this.previewDiv.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                self.previewDiv.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                self.previewDiv.querySelectorAll('.segment-preview').forEach(p => p.classList.remove('active'));

                e.target.classList.add('active');
                const targetId = `preview-${e.target.dataset.segment}`;
                const targetEl = document.getElementById(targetId);
                if(targetEl) targetEl.classList.add('active');
            });
        });
    }

    renderSegmentPreview(segment, stats, preview) {
        if (!stats) return ''; // Handle missing stats

        let html = `
            <div class="segment-stats">
                <h4>${segment} Segment Stats</h4>
                <p><strong>Total rows:</strong> ${stats.total_rows}</p>
                <p><strong>Unique symbols:</strong> ${stats.unique_symbols}</p>
        `;

        // Show instrument breakdown for FO
        if (segment === 'F&O' && Object.keys(stats.instrument_types).length > 0) {
            html += `<p><strong>Instruments:</strong> `;
            for (const [type, count] of Object.entries(stats.instrument_types)) {
                html += `${type}: ${count}, `;
            }
            html = html.slice(0, -2) + `</p>`;
        }

        html += `</div>`;

        if (preview.length > 0) {
            html += `<h4>Sample Data:</h4>`;
            html += `<div style="overflow-x:auto;"><table class="preview-table" style="width:100%; border-collapse:collapse;">`;
            html += `<thead><tr>`;

            // Headers based on segment
            if (segment === 'Cash') {
                html += `<th>Symbol</th><th>Series</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th>`;
            } else {
                html += `<th>Symbol</th><th>Type</th><th>Expiry</th><th>Strike</th><th>Option</th><th>Open</th><th>Close</th><th>OI</th>`;
            }
            html += `</tr></thead><tbody>`;

            preview.forEach(row => {
                html += `<tr>`;
                if (segment === 'Cash') {
                    html += `
                        <td>${row.symbol}</td>
                        <td>${row.series}</td>
                        <td>${row.open.toFixed(2)}</td>
                        <td>${row.high.toFixed(2)}</td>
                        <td>${row.low.toFixed(2)}</td>
                        <td>${row.close.toFixed(2)}</td>
                        <td>${row.volume.toLocaleString()}</td>
                    `;
                } else {
                    html += `
                        <td>${row.symbol}</td>
                        <td>${row.instrument_type}</td>
                        <td>${row.expiry || '-'}</td>
                        <td>${row.strike ? row.strike.toFixed(2) : '-'}</td>
                        <td>${row.option_type || '-'}</td>
                        <td>${row.open.toFixed(2)}</td>
                        <td>${row.close.toFixed(2)}</td>
                        <td>${row.open_interest ? row.open_interest.toLocaleString() : '-'}</td>
                    `;
                }
                html += `</tr>`;
            });

            html += `</tbody></table></div>`;
        } else {
            html += `<p class="no-data">No ${segment} data found in file</p>`;
        }

        return html;
    }

    async confirmImport() {
        if (!this.selectedFile || !this.previewData) return;

        // Get selected segments
        const segments = [];
        if (this.segmentCheckboxes.cm.checked) segments.push('CM');
        if (this.segmentCheckboxes.fo.checked) segments.push('FO');

        if (segments.length === 0) {
            this.showStatus('Please select at least one segment to import', 'error');
            return;
        }

        this.confirmBtn.disabled = true;
        this.showStatus('Importing data...', 'info');

        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('file_date', this.previewData.file_date);
        formData.append('overwrite_existing', this.overwriteCheckbox.checked);
        formData.append('segments', JSON.stringify(segments));

        try {
            const response = await fetch('/api/data/upload/bhavcopy/import', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                let message = `✅ Import complete: ${data.inserted} rows inserted`;
                if (data.skipped > 0) {
                    message += `, ${data.skipped} duplicates skipped`;
                }
                this.showStatus(message, 'success');

                // Clear for next import
                this.fileInput.value = '';
                this.selectedFile = null;
                this.previewData = null;
                // Keep modal open to show success? Or close?
                // Let's enable cancel to close
                this.confirmBtn.disabled = true;

            } else {
                this.showStatus('Error: ' + data.detail, 'error');
                this.confirmBtn.disabled = false;
            }
        } catch (error) {
            this.showStatus('Error importing: ' + error.message, 'error');
            this.confirmBtn.disabled = false;
        }
    }

    refreshTradingEdge() {
        // Placeholder if we need to refresh other UI components
        if (typeof Edge !== 'undefined' && Edge.fetchContext) {
            Edge.fetchContext();
        }
    }
}

const uploader = new BhavcopyUploader();
