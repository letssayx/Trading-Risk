class BhavcopyUploader {
    constructor() {
        this.previewData = null;
        this.importId = null;
        this.modal = document.getElementById('upload-modal');
        this.fileInput = document.getElementById('bhavcopy-file-input');
        this.previewArea = document.getElementById('upload-preview-area');

        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));
        }
    }

    open() {
        this.modal.style.display = 'flex';
        this.previewArea.innerHTML = '<div style="color:#888;">Select a ZIP file to upload...</div>';
        this.fileInput.value = '';
        this.previewData = null;
    }

    close() {
        this.modal.style.display = 'none';
    }

    async handleFileSelect(file) {
        if (!file) return;

        // Show Loading
        this.previewArea.innerHTML = '<div style="color:#00bcd4;">Parsing file...</div>';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/data/upload/bhavcopy', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Upload failed");
            }

            const data = await res.json();
            this.previewData = data;
            this.importId = data.import_id;
            this.renderPreview(data);

        } catch (e) {
            this.previewArea.innerHTML = `<div style="color:#f44336;">Error: ${e.message}</div>`;
        }
    }

    renderPreview(data) {
        const stats = data.stats;
        let html = `
            <div style="margin-bottom:10px; padding:10px; background:#222; border:1px solid #444;">
                <div><strong>Date:</strong> ${stats.date}</div>
                <div><strong>Total Rows:</strong> ${stats.total_rows}</div>
                <div><strong>Filtered (F&O Stocks):</strong> ${stats.filtered_rows}</div>
            </div>
            <table class="strategy-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Series</th>
                        <th>Close</th>
                        <th>Volume</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.preview.forEach(row => {
            html += `
                <tr>
                    <td>${row.symbol}</td>
                    <td>${row.series}</td>
                    <td>${row.close}</td>
                    <td>${row.total_traded_qty}</td>
                </tr>
            `;
        });

        html += `</tbody></table>
            <div style="margin-top:15px; text-align:right;">
                <button onclick="uploader.confirmImport()" style="background:#4caf50; color:#fff; border:none; padding:8px 16px; cursor:pointer;">Confirm Import</button>
            </div>
        `;

        this.previewArea.innerHTML = html;
    }

    async confirmImport() {
        if (!this.importId) return;

        this.previewArea.innerHTML = '<div style="color:#00bcd4;">Importing to database...</div>';

        try {
            const res = await fetch('/api/data/import/bhavcopy/confirm', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ import_id: this.importId })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Import failed");
            }

            const result = await res.json();
            this.previewArea.innerHTML = `<div style="color:#4caf50;">Success! Imported ${result.imported_count} records.</div>`;

            // Auto close after delay
            setTimeout(() => this.close(), 2000);

        } catch (e) {
            this.previewArea.innerHTML = `<div style="color:#f44336;">Import Error: ${e.message}</div>`;
        }
    }
}

const uploader = new BhavcopyUploader();
