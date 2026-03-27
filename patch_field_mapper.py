import re

with open("backend/ingest/field_mapper.py", "r") as f:
    code = f.read()

# Make sure we don't duplicate patches if it's already there
if "'DELTA' in upper_cols or 'DELTA FACTOR' in upper_cols" not in code:
    code = code.replace("'DELTA' in upper_cols", "'DELTA' in upper_cols or 'DELTA FACTOR' in upper_cols")
    code = code.replace("'Delta' in columns and 'Strike Price' in columns", "('DELTA' in columns or 'Delta Factor' in columns) and 'SYMBOL' in columns")
    code = code.replace("'DELTA' in upper_cols and 'SYMBOL' in upper_cols", "('DELTA' in upper_cols or 'DELTA FACTOR' in upper_cols) and 'SYMBOL' in upper_cols")

with open("backend/ingest/field_mapper.py", "w") as f:
    f.write(code)

with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

if '<label class="checkbox-label"><input type="checkbox" class="latest-type" value="contract_delta"> Contract Delta</label>' not in html:
    html = html.replace('<label class="checkbox-label"><input type="checkbox" class="latest-type" value="nse_security"> Security Master</label>', '<label class="checkbox-label"><input type="checkbox" class="latest-type" value="nse_security"> Security Master</label>\n                                <label class="checkbox-label"><input type="checkbox" class="latest-type" value="contract_delta"> Contract Delta</label>')

if '<label class="checkbox-label"><input type="checkbox" class="range-type" value="contract_delta"> Contract Delta</label>' not in html:
    html = html.replace('<label class="checkbox-label"><input type="checkbox" class="range-type" value="nse_security"> Security Master</label>', '<label class="checkbox-label"><input type="checkbox" class="range-type" value="nse_security"> Security Master</label>\n                                <label class="checkbox-label"><input type="checkbox" class="range-type" value="contract_delta"> Contract Delta</label>')

if '<option value="contract_delta">Contract Delta</option>' not in html:
    html = html.replace('<option value="nse_security">Security Master</option>', '<option value="nse_security">Security Master</option>\n                                    <option value="contract_delta">Contract Delta</option>')

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(html)
