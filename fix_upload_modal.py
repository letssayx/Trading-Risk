with open('backend/ui/static/js/uploadModal.js', 'r') as f:
    content = f.read()

# We need to make sure 'file_type' and 'file_date' aren't sent if we are using the override-xml endpoint,
# OR we simply change the upload endpoint to accept file and not require symbol/meeting_date form inputs.
# Wait, let's look at `formData`. The generic upload sends `file`, `file_type`, `file_date`.
# Let's fix uploadModal.js so it ONLY sends `file` for `board_meetings_xml`.

old_block = """        if (this.dropzoneMode) {
            const file = this.fileInput.files[0];
            const fileType = document.getElementById('uploadFileType').value;
            const fileDate = document.getElementById('uploadFileDate').value;
            formData = new FormData();
            formData.append("file", file);
            formData.append("file_type", fileType);
            if (fileDate) formData.append("file_date", fileDate);
        }

        this.startProgress(`Uploading ${file.name} as ${fileType}...`);

        try {
            let apiUrl = '/api/data/upload/generic';
            if (fileType === 'board_meetings_xml') {
                apiUrl = '/api/data/board-meetings/override-xml';
            }"""

new_block = """        if (this.dropzoneMode) {
            const file = this.fileInput.files[0];
            const fileType = document.getElementById('uploadFileType').value;
            const fileDate = document.getElementById('uploadFileDate').value;
            formData = new FormData();
            formData.append("file", file);
            if (fileType !== 'board_meetings_xml') {
                formData.append("file_type", fileType);
                if (fileDate) formData.append("file_date", fileDate);
            }
        }

        const currentFileType = document.getElementById('uploadFileType').value;
        this.startProgress(`Uploading ${file.name} as ${currentFileType}...`);

        try {
            let apiUrl = '/api/data/upload/generic';
            if (currentFileType === 'board_meetings_xml') {
                apiUrl = '/api/data/board-meetings/override-xml';
            }"""

content = content.replace(old_block, new_block)

# Let's also fix the success message extraction because the new override-xml endpoint returns:
# {"message": "Success", "data": {...}}
# whereas generic upload returns:
# {"success": True, "rows_processed": X, "date": Y}

old_success_block = """            const data = await res.json();

            if (data.success) {
                this.successProgress(`Successfully imported ${data.rows_processed} rows for ${data.date}`);
                this.renderDetails({[data.type]: {status: 'SUCCESS', rows_processed: data.rows_processed}});
            } else {
                this.failProgress("Import reported failure without error message");
            }"""

new_success_block = """            const data = await res.json();

            if (currentFileType === 'board_meetings_xml') {
                this.successProgress(`Success! Updated record. Extracted Amount: ${data.data.extracted_dividend_amount}`);
                this.renderDetails({'XML Override': {status: 'SUCCESS', rows_processed: 1}});
                // auto reload workbench data
                if (typeof loadDividendsData === 'function') {
                    loadDividendsData();
                }
            } else if (data.success) {
                this.successProgress(`Successfully imported ${data.rows_processed} rows for ${data.date}`);
                this.renderDetails({[data.type]: {status: 'SUCCESS', rows_processed: data.rows_processed}});
            } else {
                this.failProgress("Import reported failure without error message");
            }"""

content = content.replace(old_success_block, new_success_block)

with open('backend/ui/static/js/uploadModal.js', 'w') as f:
    f.write(content)
