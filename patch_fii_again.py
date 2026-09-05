import re

# Also fix the button to blue class for options analysis if it was standard
file_path = "backend/ui/templates/derivatives.html"
with open(file_path, "r") as f:
    content = f.read()

content = content.replace('<button class="btn btn-secondary" id="btn-load-options-analysis"', '<button class="btn btn-primary" id="btn-load-options-analysis"')

with open(file_path, "w") as f:
    f.write(content)
