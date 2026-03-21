import re

file_path = 'backend/ui/templates/workbench.html'
with open(file_path, 'r') as f:
    content = f.read()

# Make sure we fetch both Dividends and Board Meetings in `loadDividendsData`
# Replace the fetch part:
old_fetch = r"""        // Try fetching from our database first to support full history
        let dbActionsRes = await fetch\(`/api/data/view/list\?type=dividend\$\{limitQuery\}\$\{symbolQuery\}`\);
        let dbActions = await dbActionsRes.json\(\);

        // Always trust the database. If it's empty, we legitimately have no data for that symbol.
        let actions = dbActions\.data \|\| \[\];

        let dbMeetingsRes = await fetch\(`/api/data/view/list\?type=board_meeting\$\{limitQuery\}\$\{symbolQuery\}`\);
        let dbMeetings = await dbMeetingsRes.json\(\);
        let meetings = dbMeetings\.data \|\| \[\];"""

new_fetch = """        // Fetch dividends
        let dbActionsRes = await fetch(`/api/data/view/list?type=dividend${limitQuery}${symbolQuery}`);
        let dbActions = await dbActionsRes.json();
        let actions = dbActions.data || [];

        // Fetch board meetings to join
        let dbMeetingsRes = await fetch(`/api/data/view/list?type=board_meeting${limitQuery}${symbolQuery}`);
        let dbMeetings = await dbMeetingsRes.json();
        let meetings = dbMeetings.data || [];"""

content = re.sub(old_fetch, new_fetch, content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(content)

print("Updated loader logic for Dividends tab.")
