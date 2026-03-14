with open('backend/ui/templates/workbench.html', 'r') as f:
    html = f.read()

# Make sure JS vars exist
if 'let issueCurrentStatus =' not in html:
    html = html.replace("let caCurrentTab = 'actions';", "let caCurrentTab = 'actions';\n        let issueCurrentStatus = 'active';")

if 'function switchIssueStatus' not in html:
    func = """
        function switchIssueStatus(status) {
            issueCurrentStatus = status;
            document.querySelectorAll('.status-tab').forEach(btn => {
                btn.style.color = '#a1a1aa';
                btn.style.borderBottomColor = 'transparent';
                if(btn.dataset.status === status) {
                    btn.style.color = '#4ade80';
                    btn.style.borderBottomColor = '#4ade80';
                }
            });
            renderCorporateActionsTable();
        }
        function filterCATable() { renderCorporateActionsTable(); }
"""
    html = html.replace("function switchCATab(tab) {", func + "        function switchCATab(tab) {")

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(html)
