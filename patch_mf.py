import re
with open("backend/ui/static/js/mutualFund.js", "r") as f:
    content = f.read()

# Disable automatic loading at the bottom of the file
content = content.replace("document.addEventListener('DOMContentLoaded', () => {\n    loadMfFilters();\n});", "document.addEventListener('DOMContentLoaded', () => {\n    // loadMfFilters(); // Temporarily disabled to prevent backend errors for missing tables\n});")

with open("backend/ui/static/js/mutualFund.js", "w") as f:
    f.write(content)
