import re

file_path = "backend/ui/templates/derivatives.html"
with open(file_path, "r") as f:
    content = f.read()

# Replace all occurrences of the Force checkboxes just in case
content = re.sub(r'<label[^>]*>\s*<input[^>]*id="mwpl-force-refresh"[^>]*>\s*Force\s*</label>', '', content)

with open(file_path, "w") as f:
    f.write(content)
