import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Replace all row.field !== null ? (row.field * 100).toFixed(decimals) + '%' : '-'
def replace_pct(match):
    field = match.group(1)
    decimals = match.group(2)
    return f"(row.{field} != null && typeof row.{field} === 'number') ? (row.{field} * 100).toFixed({decimals}) + '%' : '-'"

content = re.sub(r'row\.([a-zA-Z0-9_]+)\s*!==\s*null\s*\?\s*\(row\.[a-zA-Z0-9_]+\s*\*\s*100\)\.toFixed\((\d+)\)\s*\+\s*\'%\'\s*:\s*\'-\'', replace_pct, content)

# Replace remaining percentages row.field !== null ? row.field.toFixed(decimals) + '%' : '-'
def replace_pct_direct(match):
    field = match.group(1)
    decimals = match.group(2)
    return f"(row.{field} != null && typeof row.{field} === 'number') ? row.{field}.toFixed({decimals}) + '%' : '-'"

content = re.sub(r'row\.([a-zA-Z0-9_]+)\s*!==\s*null\s*\?\s*row\.[a-zA-Z0-9_]+\.toFixed\((\d+)\)\s*\+\s*\'%\'\s*:\s*\'-\'', replace_pct_direct, content)

# Handle locales row.field !== null ? row.field.toLocaleString() : '-'
def replace_locale(match):
    field = match.group(1)
    return f"(row.{field} != null && typeof row.{field} === 'number') ? row.{field}.toLocaleString() : '-'"

content = re.sub(r'row\.([a-zA-Z0-9_]+)\s*!==\s*null\s*\?\s*row\.[a-zA-Z0-9_]+\.toLocaleString\(\)\s*:\s*\'-\'', replace_locale, content)

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
