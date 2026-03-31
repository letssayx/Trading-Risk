# The HTML I added might break if the replaced string wasn't EXACT.
# Let's check `backend/ui/templates/workbench.html` to see if the buttons were successfully added.
with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

print("matrix_btn added:", "exportTableToCSV('matrix-table'" in html)
print("basis_btn added:", "exportTableToCSV('basis-table'" in html)
print("chain_btn added:", "exportTableToCSV('opt-chain-table'" in html)
print("mwpl_btn added:", "exportTableToCSV('mwpl-table'" in html)
print("rollover_btn added:", "exportTableToCSV('rollover-table'" in html)
print("oi_pcr_btn added:", "exportChartDataToCSV(window.pcrChartInstance" in html)
