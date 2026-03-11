import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# 1. Remove Check Status Button
old_status_btn = '<button id="mr-status-btn" class="btn btn-secondary" style="margin-left: 10px;">Check Status</button>'
content = content.replace(old_status_btn, '')

# 2. Remove Download Table Button from side panel
old_export_btn_side = '<button id="mr-export-btn" class="btn btn-secondary" style="margin-left: 10px;">Download Table (CSV)</button>'
content = content.replace(old_export_btn_side, '')

# 3. Add Download Table Button inline next to Load Timeseries
old_inline_search = '<button id="mr-fetch-ts-btn" class="btn btn-secondary" style="padding: 4px 10px;">Load Timeseries</button>'
new_inline_search = '<button id="mr-fetch-ts-btn" class="btn btn-secondary" style="padding: 4px 10px;">Load Timeseries</button>\n                        <button id="mr-export-btn" class="btn btn-secondary" style="padding: 4px 10px; margin-left: 10px;">Download CSV</button>'
content = content.replace(old_inline_search, new_inline_search)

# 4. Remove the Check Status Event Listener
start_status_logic = content.find("// Status Check Button Logic")
if start_status_logic != -1:
    end_status_logic = content.find("});", start_status_logic) + 3
    content = content[:start_status_logic] + content[end_status_logic:]

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
