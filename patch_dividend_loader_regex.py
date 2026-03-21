import re

file_path = 'backend/ui/templates/workbench.html'
with open(file_path, 'r') as f:
    content = f.read()

pattern = re.compile(r'// Try fetching from our database first to support full history.*?let dbMeetings = await dbMeetingsRes\.json\(\);', re.DOTALL)

def replace(m):
    return """// Fetch dividends
        let dbActionsRes = await fetch(`/api/data/view/list?type=dividend${limitQuery}${symbolQuery}`);
        let dbActions = await dbActionsRes.json();

        // Always trust the database. If it's empty, we legitimately have no data for that symbol.
        let actions = dbActions.data || [];

        // Fetch board meetings to join
        let dbMeetingsRes = await fetch(`/api/data/view/list?type=board_meeting${limitQuery}${symbolQuery}`);
        let dbMeetings = await dbMeetingsRes.json();"""

content = pattern.sub(replace, content)

with open(file_path, 'w') as f:
    f.write(content)

print("regex matched")
