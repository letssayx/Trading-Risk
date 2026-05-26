with open('backend/ui/static/js/uploadModal.js', 'r') as f:
    content = f.read()

new_content = content.replace(
'''        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("file_type", fileType);
        if (fileDate) formData.append("file_date", fileDate);''',
'''        const file = fileInput.files[0];
        const formData = new FormData();

        if (fileType === 'board_meetings_xml') {
            const sym = prompt("Enter Symbol for this XML override (e.g. MPHASIS):");
            if (!sym) {
                alert("Symbol is required for XML override.");
                return;
            }
            // Use the date from the date picker if provided, otherwise ask
            let bDate = fileDate;
            if (!bDate) {
                bDate = prompt("Enter Meeting Date (DD-MMM-YYYY) for this XML override:");
                if (!bDate) {
                    alert("Meeting Date is required for XML override.");
                    return;
                }
            } else {
                 // Convert YYYY-MM-DD to DD-MMM-YYYY
                 const dParts = bDate.split('-');
                 if (dParts.length === 3) {
                     const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                     bDate = `${dParts[2]}-${months[parseInt(dParts[1])-1]}-${dParts[0]}`;
                 }
            }
            formData.append("file", file);
            formData.append("symbol", sym);
            formData.append("meeting_date", bDate);
        } else {
            formData.append("file", file);
            formData.append("file_type", fileType);
            if (fileDate) formData.append("file_date", fileDate);
        }'''
)

with open('backend/ui/static/js/uploadModal.js', 'w') as f:
    f.write(new_content)
