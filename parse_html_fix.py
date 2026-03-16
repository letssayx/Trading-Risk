with open('backend/ui/templates/workbench.html', 'r') as f:
    text = f.read()

# For Timeseries, Date and Symbol must have the correct styling
search = '<th style="text-align: left; position: sticky; top: 0; left: 90px; background: #1e1e1e; z-index: 3;">Symbol</th>'
replace = '<th style="text-align: left; position: sticky; top: 0; left: 90px; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Symbol</th>'

if search in text:
    text = text.replace(search, replace)
    with open('backend/ui/templates/workbench.html', 'w') as f:
        f.write(text)
    print("Patched Symbol width in timeseries.")
else:
    print("Search string not found")
