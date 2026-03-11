import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Let's ensure the generateTableHTML is properly exposed and not shadowed or duplicated inside loadTimeseriesData
count = content.count('const generateTableHTML =')
print(f"Count of generateTableHTML: {count}")
