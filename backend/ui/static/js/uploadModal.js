class BhavcopyUploader {
    constructor() {
        this.modal = document.getElementById('bhavcopy-upload-modal');
        this.previewArea = document.getElementById('upload-preview');
        this.statusArea = document.getElementById('upload-status');
        this.fileInput = document.getElementById('bhavcopy-file');

        // No form element in updated HTML structure, relying on inputs
        this.init();
    }

    init() {
        // Close buttons
        const closeBtn = this.modal.querySelector('.close');
        if(closeBtn) closeBtn.onclick = () => this.close();

        const closeFooterBtn = document.getElementById('close-import-btn');
        if(closeFooterBtn) closeFooterBtn.onclick = () => this.close();

        // Confirm Import Button (Static in footer)
        const confirmBtn = document.getElementById('confirm-import-btn');
        if(confirmBtn) confirmBtn.onclick = () => this.handleImport();

        // File Input Change -> Auto Preview
        this.fileInput.addEventListener('change', () => {
            if(this.fileInput.files.length > 0) {
                this.handlePreview();
            }
        });

        // Mode Switch
        const modeRadios = document.querySelectorAll('input[name="import-mode"]');
        const hint = document.getElementById('file-hint');
        modeRadios.forEach(r => r.addEventListener('change', (e) => {
            if(e.target.value === 'historical') {
                hint.innerText = "Expected format: Any valid UDIFF ZIP/CSV for past years.";
            } else {
                hint.innerText = "Expected format: BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip";
            }
        }));

        // Segment Type Switch - Trigger re-preview
        const segTypeRadios = document.querySelectorAll('input[name="file-segment-type"]');
        segTypeRadios.forEach(r => r.addEventListener('change', () => {
             if(this.fileInput.files.length > 0) {
                this.handlePreview();
            }
        }));

        // ESC Key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'block') {
                this.close();
            }
        });

        // Click outside
        window.onclick = (e) => {
            if (e.target == this.modal) {
                this.close();
            }
        }
    }

    open() {
        this.modal.style.display = 'block';
        this.reset();
    }

    close() {
        this.modal.style.display = 'none';
    }

    reset() {
        this.fileInput.value = '';
        this.previewArea.innerHTML = '<p class="placeholder" style="color:#888;">Select a file to see preview</p>';
        this.statusArea.innerHTML = '';
        document.getElementById('confirm-import-btn').disabled = true;
        this.currentFileDate = null;
    }

    async handlePreview() {
        const file = this.fileInput.files[0];
        if(!file) return;

        // Get selected segment type
        const segVal = document.querySelector('input[name="file-segment-type"]:checked').value;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_segment_type', segVal);

        this.statusArea.innerHTML = 'Analyzing file...';
        this.previewArea.innerHTML = '<div class="loader">Loading preview...</div>';

        // Disable import until preview success
        document.getElementById('confirm-import-btn').disabled = true;

        try {
            const res = await fetch('/api/data/upload/bhavcopy/preview', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if(!res.ok) throw new Error(data.detail || 'Preview failed');

            this.renderPreview(data);
            this.statusArea.innerHTML = '';

            // Enable Import Button explicitly
            const btn = document.getElementById('confirm-import-btn');
            if(btn) {
                btn.disabled = false;
                btn.style.cursor = 'pointer'; // Visual feedback
            }

        } catch(e) {
            this.statusArea.innerHTML = `<div class="error" style="color:#f44336; padding:10px; border:1px solid red;">Error: ${e.message}</div>`;
            this.previewArea.innerHTML = '';
            const btn = document.getElementById('confirm-import-btn');
            if(btn) btn.disabled = true;
        }
    }

    renderPreview(data) {
        this.currentFileDate = data.file_date;
        const overwriteCheck = document.getElementById('overwrite-existing');

        // Auto-check overwrite if data exists
        if(data.warnings.date_exists) {
            overwriteCheck.checked = true;
        }

        let html = `
            <div class="preview-summary">
                <h4>File Analysis: ${data.filename}</h4>
                <p>Date Detected: <strong>${data.file_date || 'Unknown'}</strong></p>
                <div class="stats-grid" style="display:flex; gap:20px; margin-top:10px;">
        `;

        const segVal = document.querySelector('input[name="file-segment-type"]:checked').value;
        const segmentsToShow = (segVal === 'BOTH') ? ['CM', 'FO'] : [segVal];

        for(let seg of segmentsToShow) {
            const s = data.stats[seg];
            if(s) {
                html += `
                    <div class="stat-box" style="background:#333; padding:10px; border-radius:4px; flex:1;">
                        <h5 style="margin:0 0 5px 0; border-bottom:1px solid #555;">${seg} Segment</h5>
                        <div style="font-size:0.9em;">
                            Rows: ${s.total_rows}<br>
                            Symbols: ${s.unique_symbols}
                        </div>
                    </div>
                `;
            } else {
                 html += `
                    <div class="stat-box" style="background:#333; padding:10px; border-radius:4px; flex:1; opacity: 0.5;">
                        <h5 style="margin:0 0 5px 0; border-bottom:1px solid #555;">${seg} Segment</h5>
                        <div style="font-size:0.9em;">Not found in file</div>
                    </div>
                `;
            }
        }

        html += `</div>`;

        if(data.warnings.date_exists) {
            html += `<div class="warning-box" style="margin-top:10px; color:#ff9800; border:1px solid #ff9800; padding:5px;">Warning: Data for ${data.file_date} already exists! Overwrite is checked.</div>`;
        } else if (data.warnings.already_imported) {
             html += `<div class="warning-box" style="margin-top:10px; color:#2196f3; border:1px solid #2196f3; padding:5px;">Note: This file name was imported on ${data.warnings.previous_import_date}.</div>`;
        }

        html += `</div>`;
        this.previewArea.innerHTML = html;
    }

    async handleImport() {
        const file = this.fileInput.files[0];
        if(!file) return;

        // Gather options
        const overwrite = document.getElementById('overwrite-existing').checked;
        const mode = document.querySelector('input[name="import-mode"]:checked').value;
        const segVal = document.querySelector('input[name="file-segment-type"]:checked').value;

        const segments = [];
        if(segVal === 'CM' || segVal === 'BOTH') segments.push('CM');
        if(segVal === 'FO' || segVal === 'BOTH') segments.push('FO');

        if(segments.length === 0) {
            alert("Please select at least one segment to import.");
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_date', this.currentFileDate || ''); // If null, backend tries to derive
        formData.append('overwrite_existing', overwrite);
        formData.append('segments', JSON.stringify(segments));
        formData.append('mode', mode);

        this.statusArea.innerHTML = 'Importing... This may take a moment.';
        document.getElementById('confirm-import-btn').disabled = true;

        try {
            const res = await fetch('/api/data/upload/bhavcopy/import', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();

            if(!res.ok) {
                // Handle object error messages
                let msg = result.detail || 'Import failed';
                if(typeof msg === 'object') msg = JSON.stringify(msg);
                throw new Error(msg);
            }

            let successMsg = `Successfully imported ${result.inserted} records!`;

            if(result.skipped > 0) {
                 successMsg += `<br><small style="color:#ff9800">Skipped ${result.skipped} rows.</small>`;
                 if(result.skipped_reasons) {
                    successMsg += `<div style="font-size:0.8em; color:#ccc; margin-top:5px; max-height:100px; overflow-y:auto;">
                        <strong>Skip Reasons:</strong><br>
                        ${Object.entries(result.skipped_reasons).map(([k,v]) => `${k}: ${v}`).join('<br>')}
                    </div>`;
                 }
            }

            if(result.errors && result.errors.length > 0) {
                successMsg += `<br><small style="color:#f44336">${result.errors.length} file errors (check console)</small>`;
                console.warn("Import Errors:", result.errors);
            }

            this.statusArea.innerHTML = `<div class="success" style="color:#4caf50; font-weight:bold; margin-top:10px;">${successMsg}</div>`;

            // Disable button to prevent double submit
            document.getElementById('confirm-import-btn').disabled = true;

        } catch(e) {
            this.statusArea.innerHTML = `<div class="error" style="color:#f44336; margin-top:10px;">Import Error: ${e.message}</div>`;
            document.getElementById('confirm-import-btn').disabled = false;
        }
    }
}

// Initialize
window.uploader = new BhavcopyUploader();
