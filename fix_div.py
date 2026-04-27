with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Line 2779 is the closing div for `tab-content-area`
# Let's verify by just removing the extra closing div and seeing if counts match

import re
html_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
lines = html_no_comments.split('\n')
count = 0
for i, line in enumerate(lines):
    count += line.count('<div')
    count -= line.count('</div')
print("Div count mismatch:", count)

# Actually, let's fix the extra closing div on line 2779. Wait, there's `app-container` and `tab-content-area`?
# Let's count where `tab-terminal` ends.
