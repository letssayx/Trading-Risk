import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Replace all row.field.toFixed to safely handle undefined/null and typeof number
def replace_to_fixed(match):
    field = match.group(1)
    decimals = match.group(2)
    # create a safe fallback format: row.field != null && typeof row.field === 'number' ? row.field.toFixed(...) : '-'
    return f"(row.{field} != null && typeof row.{field} === 'number') ? row.{field}.toFixed({decimals}) : '-'"

content = re.sub(r'row\.([a-zA-Z0-9_]+)\s*!==\s*null\s*\?\s*row\.[a-zA-Z0-9_]+\.toFixed\((\d+)\)\s*:\s*\'-\'', replace_to_fixed, content)

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
