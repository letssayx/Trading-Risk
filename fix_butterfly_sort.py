import re

file_path = "backend/ui/static/js/script_workbench2.js"
with open(file_path, "r") as f:
    content = f.read()

# Fix the butterfly sort in market activity too
search = "const strikes = Object.keys(latest.high_oi_strikes).map(Number).sort((a,b) => a - b);"
replace = "const strikes = Object.keys(latest.high_oi_strikes).map(Number).sort((a,b) => b - a);"

content = content.replace(search, replace)

with open(file_path, "w") as f:
    f.write(content)
