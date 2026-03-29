import re

html_file = 'backend/ui/templates/workbench.html'

with open(html_file, 'r') as f:
    html_content = f.read()

# Make sure opt_analysis.js is included in the head or at the end
if 'opt_analysis.js' not in html_content:
    html_content = html_content.replace(
        '<script src="/static/js/chartTabs.js"></script>',
        '<script src="/static/js/chartTabs.js"></script>\n    <script src="/static/js/opt_analysis.js"></script>'
    )

with open(html_file, 'w') as f:
    f.write(html_content)
