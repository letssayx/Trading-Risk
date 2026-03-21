import re
with open('backend/ui/templates/workbench.html', 'r') as f:
    text = f.read()
if "setupAutocomplete" in text and "currentFocus" in text and "e.key === 'Enter'" in text:
    print("Patch successful!")
else:
    print("Patch failed.")
