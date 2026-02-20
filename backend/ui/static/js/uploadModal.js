class BhavcopyUploader {
    constructor() {
        this.modal = document.getElementById('upload-bhavcopy-modal');
        this.previewArea = document.getElementById('upload-preview');
        this.statusArea = document.getElementById('upload-status');
        this.fileInput = document.getElementById('bhavcopy-file');
        this.form = document.getElementById('bhavcopy-upload-form');

        this.currentFileDate = null;
        this.segments = ['CM', 'FO'];

        this.init();
    }

    init() {
        // Event Listeners
        if(this.form) {
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handlePreview();
            });
        }

        // Close button scoping
        const closeBtn = this.modal.querySelector('.close');
        if(closeBtn) {
            closeBtn.onclick = () => this.close();
        }

        // Import Button (dynamic)
        document.addEventListener('click', (e) => {
            if(e.target && e.target.id === 'btn-confirm-import') {
                this.handleImport();
            }
        });

        // Add ESC key listener
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
        this.form.reset();
        this.previewArea.innerHTML = '';
        this.statusArea.innerHTML = '';
        this.currentFileDate = null;
    }

    async handlePreview() {
        const file = this.fileInput.files[0];
        if(!file) return;

        const formData = new FormData();
        formData.append('file', file);

        this.statusArea.innerHTML = 'Analyzing file...';

        try {
            const res = await fetch('/api/data/upload/bhavcopy/preview', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if(!res.ok) throw new Error(data.detail || 'Preview failed');

            this.renderPreview(data);
            this.statusArea.innerHTML = '';

        } catch(e) {
            this.statusArea.innerHTML = `<div class="error">Error: ${e.message}</div>`;
        }
    }

    renderPreview(data) {
        this.currentFileDate = data.file_date;

        let html = `
            <div class="preview-summary">
                <h4>File Analysis: ${data.filename}</h4>
                <p>Date Detected: <strong>${data.file_date || 'Unknown'}</strong></p>
                <div class="stats-grid">
        `;

        for(let seg of ['CM', 'FO']) {
            const s = data.stats[seg];
            if(s) {
                html += `
                    <div class="stat-box">
                        <h5>${seg} Segment</h5>
                        <p>Rows: ${s.total_rows}</p>
                        <p>Symbols: ${s.unique_symbols}</p>
                    </div>
                `;
            }
        }

        html += `</div>`;

        if(data.warnings.date_exists) {
            html += `<div class="warning-box">Warning: Data for ${data.file_date} already exists!</div>`;
        }

        html += `
            <div class="import-controls">
                <label>
                    <input type="checkbox" id="overwrite-check" ${data.warnings.date_exists ? 'checked' : ''}>
                    Overwrite existing data
                </label>
                <button id="btn-confirm-import" class="btn-primary">Confirm Import</button>
            </div>
        `;

        this.previewArea.innerHTML = html;
    }

    async handleImport() {
        const file = this.fileInput.files[0];
        const overwrite = document.getElementById('overwrite-check').checked;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_date', this.currentFileDate);
        formData.append('overwrite_existing', overwrite);
        formData.append('segments', JSON.stringify(['CM', 'FO']));

        this.statusArea.innerHTML = 'Importing... This may take a moment.';
        document.getElementById('btn-confirm-import').disabled = true;

        try {
            const res = await fetch('/api/data/upload/bhavcopy/import', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();

            if(!res.ok) throw new Error(result.detail || 'Import failed');

            this.statusArea.innerHTML = `<div class="success">Successfully imported ${result.inserted} records!</div>`;
            setTimeout(() => this.close(), 2000);

        } catch(e) {
            this.statusArea.innerHTML = `<div class="error">Import Error: ${e.message}</div>`;
            document.getElementById('btn-confirm-import').disabled = false;
        }
    }
}

// Initialize
window.uploader = new BhavcopyUploader();
