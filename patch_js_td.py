with open('backend/ui/templates/workbench.html', 'r') as f:
    text = f.read()

# Make sure the `td` matches `th` width in generateTableHTML
# For snapshot, Symbol is left: 0
# For timeseries, Date is left: 0, Symbol is left: 90px.
search = """                            if(!isSnapshot) {
                                html += `<td style="position: sticky; left: 0; background: #1e1e1e; z-index: 2;">${row.trade_date}</td>`;
                                html += `<td style="position: sticky; left: 90px; background: #1e1e1e; z-index: 2;">${row.symbol}</td>`;
                            } else {
                                html += `<td style="position: sticky; left: 0; background: #1e1e1e; z-index: 2;">${row.symbol}</td>`;
                            }"""

replace = """                            if(!isSnapshot) {
                                html += `<td style="position: sticky; left: 0; background: #1e1e1e; z-index: 2; min-width: 90px; max-width: 90px; width: 90px;">${row.trade_date}</td>`;
                                html += `<td style="position: sticky; left: 90px; background: #1e1e1e; z-index: 2; min-width: 90px; max-width: 90px; width: 90px;">${row.symbol}</td>`;
                            } else {
                                html += `<td style="position: sticky; left: 0; background: #1e1e1e; z-index: 2;">${row.symbol}</td>`;
                            }"""

if search in text:
    text = text.replace(search, replace)
    with open('backend/ui/templates/workbench.html', 'w') as f:
        f.write(text)
    print("Patched TD width in generateTableHTML.")
else:
    print("TD Search string not found")
