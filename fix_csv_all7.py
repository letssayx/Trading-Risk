import re

with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

# Add button to Data Matrix
btn_matrix = """<button class="btn btn-secondary" onclick="exportTableToCSV('mr-data-table', 'Data_Matrix')"><i class="fas fa-download"></i> CSV</button>"""
# Find where to put it. `Data Matrix` header is `<h2 style="margin: 0; color: #fff; font-size: 18px;">Data Matrix</h2>`
if btn_matrix not in html:
    html = html.replace('<h2 style="margin: 0; color: #fff; font-size: 18px;">Data Matrix</h2>', '<h2 style="margin: 0; color: #fff; font-size: 18px;">Data Matrix</h2>\n                        ' + btn_matrix)

# Add button to Basis Watch
btn_watch = """<button class="btn btn-secondary" onclick="exportTableToCSV('marketwatch-table', 'Basis_Watch')"><i class="fas fa-download"></i> CSV</button>"""
if btn_watch not in html:
    # `Basis Watch (Derivatives)`
    html = html.replace('<button class="btn btn-secondary" onclick="loadMarketWatch()"><i class="fas fa-sync"></i> Refresh Data</button>', '<button class="btn btn-secondary" onclick="loadMarketWatch()"><i class="fas fa-sync"></i> Refresh Data</button>\n                            ' + btn_watch)

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(html)
print("Added missing buttons")
