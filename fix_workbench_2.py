with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Make the manual modal UI hide symbol and date as well? Wait, we can't because the route now ONLY takes xml_url and parses it automatically!
# So the user doesn't need to input symbol and date manually. Let's fix the modal HTML!

# HTML patch
old_html = """    <div class="modal-content" style="width: 400px;">
        <h3>Override Board Meeting Data from XML</h3>
        <p style="font-size: 0.9em; color: #ccc;">Enter the details and the URL of the XBRL XML file from NSE to manually parse missing dividend details.</p>

        <label for="xml-symbol" style="display:block; margin-top:10px;">Symbol:</label>
        <input type="text" id="xml-symbol" placeholder="e.g. MPHASIS" style="width: 100%; padding: 8px; margin-top: 5px; background: #333; color: white; border: 1px solid #555; border-radius: 4px;" />

        <label for="xml-meeting-date" style="display:block; margin-top:10px;">Meeting Date (DD-MMM-YYYY):</label>
        <input type="text" id="xml-meeting-date" placeholder="e.g. 29-Apr-2026" style="width: 100%; padding: 8px; margin-top: 5px; background: #333; color: white; border: 1px solid #555; border-radius: 4px;" />

        <label for="xml-path" style="display:block; margin-top:10px;">XML File URL:</label>
        <input type="text" id="xml-path" placeholder="https://www.nseindia.com/..." style="width: 100%; padding: 8px; margin-top: 5px; background: #333; color: white; border: 1px solid #555; border-radius: 4px;" />"""

new_html = """    <div class="modal-content" style="width: 400px;">
        <h3>Override Board Meeting Data from XML</h3>
        <p style="font-size: 0.9em; color: #ccc;">Enter the URL of the XBRL XML file from NSE to manually parse missing dividend details.</p>

        <label for="xml-path" style="display:block; margin-top:10px;">XML File URL:</label>
        <input type="text" id="xml-path" placeholder="https://www.nseindia.com/..." style="width: 100%; padding: 8px; margin-top: 5px; background: #333; color: white; border: 1px solid #555; border-radius: 4px;" />"""
content = content.replace(old_html, new_html)

# JS Patch
old_js = """    async function submitXmlOverride() {
        const symbol = document.getElementById('xml-symbol').value.trim().toUpperCase();
        const meetingDate = document.getElementById('xml-meeting-date').value;
        const xmlPath = document.getElementById('xml-path').value.trim();

        if (!symbol || !meetingDate || !xmlPath) {
            alert('Please fill in all fields (Symbol, Meeting Date, and XML URL/Path).');
            return;
        }"""

new_js = """    async function submitXmlOverride() {
        const xmlPath = document.getElementById('xml-path').value.trim();

        if (!xmlPath) {
            alert('Please provide the XML URL/Path.');
            return;
        }"""
content = content.replace(old_js, new_js)

old_alert = """                alert(`Success! Updated record for ${symbol}.\n` +"""
new_alert = """                alert(`Success! Updated record.\n` +"""
content = content.replace(old_alert, new_alert)

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
