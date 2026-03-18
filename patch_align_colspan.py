import re

with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
    js = f.read()

# Update colspan to match the total count of 52
js = re.sub(r'colspan="\$\{snapshotMode \? \d+ : \d+\}"', 'colspan="${snapshotMode ? 51 : 52}"', js)

with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
    f.write(js)
print("Updated colspan.")
