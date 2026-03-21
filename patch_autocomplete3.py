import re

file_path = 'backend/ui/templates/workbench.html'
with open(file_path, 'r') as f:
    content = f.read()

css_block = """
        .autocomplete-active {
            background-color: var(--secondary-color) !important;
            color: var(--text-color);
        }
"""
# insert inside style tag
if ".autocomplete-active" not in content[:content.find('</style>')]:
    content = content.replace("</style>", css_block + "\n    </style>")
    with open(file_path, 'w') as f:
        f.write(content)
    print("CSS injected successfully")
else:
    print("CSS already exists")
