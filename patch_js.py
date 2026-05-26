with open('backend/ui/static/js/uploadModal.js', 'r') as f:
    content = f.read()

new_content = content.replace(
'''        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("file_type", fileType);
        if (fileDate) formData.append("file_date", fileDate);''',
'''        let formData = new FormData();

        if (fileType === 'board_meetings_xml') {
            const sym = prompt("Enter Symbol for this XML override (e.g. MPHASIS):");
            if (!sym) {
                alert("Symbol is required for XML override.");
                return;
            }
            const dateInput = prompt("Enter Meeting Date (DD-MMM-YYYY) for this XML override:");
            if (!dateInput) {
                alert("Meeting Date is required for XML override.");
                return;
            }

            // For XML override we just need the text contents of the URL, but the user is providing a URL inside a file or a raw XML file?
            // Since the API expects an xml_url string as Form Data, we'll ask the user for the URL directly if they selected this option,
            // OR if they uploaded an XML file, we'd have to parse it.
            // WAIT - the API `override-xml` expects `xml_url: str = Form(...)`. The user is trying to UPLOAD a file via `importManual()`.

            // Let's modify the flow. If it's `board_meetings_xml`, the user might have pasted the URL in a prompt or we should just accept the uploaded XML file directly instead of a URL.
            // Let's re-write the backend to accept an uploaded XML file OR a URL!
        } else {
            const file = fileInput.files[0];
            formData.append("file", file);
            formData.append("file_type", fileType);
            if (fileDate) formData.append("file_date", fileDate);
        }'''
)

with open('backend/ui/static/js/uploadModal.js', 'w') as f:
    f.write(new_content)
