import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# We need to completely rewrite the generateTableHTML function and the table headers.
# Let's write a python script to find and replace the entire function and headers.

# Let's extract everything from const generateTableHTML = (row, isSnapshot) => { to the end of the script tag, and rebuild it.
