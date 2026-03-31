import re

with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

# I will systematically add `<button class="btn btn-secondary" onclick="exportTableToCSV('TABLENAME', 'FILENAME')"><i class="fas fa-download"></i> CSV</button>`
# or `exportChartDataToCSV(CHARTNAME, 'FILENAME')`

def add_button(html, parent_id, btn_code, match_str):
    # Usually we add it to a header div above the table/chart
    if btn_code not in html:
        # Try to find the heading or the container
        # This is tricky without seeing the DOM.
        return False
    return True

# I will use string replacements for specific known DOM elements.
# Data Matrix: `<table class="data-table" id="matrix-table">`
matrix_btn = """<button class="btn btn-secondary" style="position:absolute; right:15px; top:15px;" onclick="exportTableToCSV('matrix-table', 'Data_Matrix')"><i class="fas fa-download"></i> CSV</button>"""
if matrix_btn not in html:
    html = html.replace('<div id="deriv-tab-matrix"', '<div id="deriv-tab-matrix" style="position:relative;"')
    html = html.replace('<div id="deriv-tab-matrix" style="position:relative;" class="deriv-sub-tab"', '<div id="deriv-tab-matrix" style="position:relative;" class="deriv-sub-tab"\n' + matrix_btn)

# Basis Watch: `<table class="data-table" id="basis-table">`
basis_btn = """<button class="btn btn-secondary" style="position:absolute; right:15px; top:15px;" onclick="exportTableToCSV('basis-table', 'Basis_Watch')"><i class="fas fa-download"></i> CSV</button>"""
if basis_btn not in html:
    html = html.replace('<div id="deriv-tab-basis"', '<div id="deriv-tab-basis" style="position:relative;"')
    html = html.replace('<div id="deriv-tab-basis" style="position:relative;" class="deriv-sub-tab"', '<div id="deriv-tab-basis" style="position:relative;" class="deriv-sub-tab"\n' + basis_btn)

# Option Chain: `<table class="data-table" id="opt-chain-table">`
chain_btn = """<button class="btn btn-secondary" style="position:absolute; right:15px; top:15px;" onclick="exportTableToCSV('opt-chain-table', 'Option_Chain')"><i class="fas fa-download"></i> CSV</button>"""
if chain_btn not in html:
    html = html.replace('<div id="deriv-tab-chain"', '<div id="deriv-tab-chain" style="position:relative;"')
    html = html.replace('<div id="deriv-tab-chain" style="position:relative;" class="deriv-sub-tab"', '<div id="deriv-tab-chain" style="position:relative;" class="deriv-sub-tab"\n' + chain_btn)

# MWPL Analysis: `<table class="data-table" id="mwpl-table">`
mwpl_btn = """<button class="btn btn-secondary" style="position:absolute; right:15px; top:15px;" onclick="exportTableToCSV('mwpl-table', 'MWPL_Analysis')"><i class="fas fa-download"></i> CSV</button>"""
if mwpl_btn not in html:
    html = html.replace('<div id="deriv-tab-mwpl"', '<div id="deriv-tab-mwpl" style="position:relative;"')
    html = html.replace('<div id="deriv-tab-mwpl" style="position:relative;" class="deriv-sub-tab"', '<div id="deriv-tab-mwpl" style="position:relative;" class="deriv-sub-tab"\n' + mwpl_btn)

# Rollover Analysis: `<table class="data-table" id="rollover-table">`
rollover_btn = """<button class="btn btn-secondary" style="position:absolute; right:15px; top:15px;" onclick="exportTableToCSV('rollover-table', 'Rollover_Analysis')"><i class="fas fa-download"></i> CSV</button>"""
if rollover_btn not in html:
    html = html.replace('<div id="deriv-tab-rollover"', '<div id="deriv-tab-rollover" style="position:relative;"')
    html = html.replace('<div id="deriv-tab-rollover" style="position:relative;" class="deriv-sub-tab"', '<div id="deriv-tab-rollover" style="position:relative;" class="deriv-sub-tab"\n' + rollover_btn)

# OI Analysis Charts
oi_pcr_btn = """<button class="btn btn-secondary" onclick="exportChartDataToCSV(window.pcrChartInstance || pcrChartInstance, 'PCR_Chart')"><i class="fas fa-download"></i> CSV</button>"""
if oi_pcr_btn not in html:
    html = html.replace('id="opt-analysis-pcr-chart"', 'id="opt-analysis-pcr-chart"\n' + oi_pcr_btn)

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(html)
print("Added CSV buttons.")
