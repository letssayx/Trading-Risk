import re

file_path = 'backend/ui/templates/workbench.html'
with open(file_path, 'r') as f:
    content = f.read()

# Let's ensure the CSS handles autocomplete-active
css_block = """
.autocomplete-active {
    background-color: var(--secondary-color) !important;
    color: var(--text-color);
}
"""

if "autocomplete-active" not in content:
    content = content.replace("</style>", css_block + "\n    </style>")
    with open(file_path, 'w') as f:
        f.write(content)
    print("Added CSS.")
else:
    print("CSS already there.")
