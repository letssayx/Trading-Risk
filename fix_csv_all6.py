import re

with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

# I will add the missing CSV buttons for Basis Watch and Data Matrix
# The tabs are:
# `deriv-tab-matrix` -> `data-table` id="derivatives-table" or something?
# Let's check the table ID for matrix.
match_matrix = re.search(r'<table[^>]*id="([^"]+)"', html[html.find('deriv-tab-matrix'):html.find('deriv-tab-watch')])
if match_matrix:
    print("Matrix Table ID:", match_matrix.group(1))

match_watch = re.search(r'<table[^>]*id="([^"]+)"', html[html.find('deriv-tab-watch'):html.find('deriv-tab-options')])
if match_watch:
    print("Basis Watch Table ID:", match_watch.group(1))

# Option chain is:
# `exportTableToCSV('option-chain-table', 'Option_Chain')` already exists!
# OI Analysis is:
# `exportTableToCSV('oi-tool-table', 'OI_Analysis')` already exists!
# Rollover and MWPL have `mwpl-table` and `rollover-table` buttons that I just added!
