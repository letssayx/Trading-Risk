import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    text = f.read()

search = """                        <button id="mr-fetch-ts-btn" class="btn btn-secondary" style="padding: 4px 10px;">Load Timeseries</button>
                        <button id="mr-export-btn" class="btn btn-secondary" style="padding: 4px 10px; margin-left: 10px;">Download CSV</button>"""

replace = """                        <button id="mr-fetch-ts-btn" class="btn btn-secondary" style="padding: 4px 10px;">Load Timeseries</button>
                        <button id="mr-clear-ts-btn" class="btn btn-secondary" style="padding: 4px 10px; margin-left: 5px;">Clear (All Scrips)</button>
                        <button id="mr-export-btn" class="btn btn-secondary" style="padding: 4px 10px; margin-left: 10px;">Download CSV</button>"""

if search in text:
    text = text.replace(search, replace)
    with open('backend/ui/templates/workbench.html', 'w') as f:
        f.write(text)
    print("Added Clear button to UI.")
else:
    print("Search block not found.")
