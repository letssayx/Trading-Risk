with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# I need to fix the submitXMLOverride to use FormData instead of query string
# because the backend endpoint changed to just taking a file or xml_url as form parameters!
# Wait, actually my python script in update_route.py removed symbol and meeting_date from the backend.
# The URL submit is in `submitXMLOverride` in workbench.html!

old_block = """        try {
            const res = await fetch(`/api/data/board-meetings/override-xml?symbol=${encodeURIComponent(symbol)}&meeting_date=${encodeURIComponent(meetingDate)}&xml_path=${encodeURIComponent(xmlPath)}`, {
                method: 'POST'
            });"""

new_block = """        try {
            const formData = new FormData();
            formData.append('xml_url', xmlPath);
            const res = await fetch(`/api/data/board-meetings/override-xml`, {
                method: 'POST',
                body: formData
            });"""

content = content.replace(old_block, new_block)

# Remove the SSRF vulnerability in backend route
# and fix the missing `symbol` and `meeting_date` query which workbench is still asking in prompts?
# Actually wait! The user rejected the prompts for the upload functionality, but the `submitXMLOverride` in workbench.html still has them!
with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
