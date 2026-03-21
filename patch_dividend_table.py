import re

file_path = 'backend/ui/templates/workbench.html'
with open(file_path, 'r') as f:
    content = f.read()

old_headers = """                            <thead>
                                <tr>
                                    <th>Broadcast Date</th>
                                    <th>Board Meeting Date</th>
                                    <th>Purpose</th>
                                    <th style="cursor: pointer;" onclick="sortDividends('ex_date')">Ex-date <span id="sort-icon-ex_date">▼</span></th>
                                    <th style="cursor: pointer;" onclick="sortDividends('symbol')">Symbol <span id="sort-icon-symbol"></span></th>
                                    <th>Amount</th>
                                    <th>Type</th>
                                    <th>Facevalue</th>
                                    <th>Purpose</th>
                                    <th>Record Date</th>
                                </tr>
                            </thead>"""

new_headers = """                            <thead>
                                <tr>
                                    <th style="cursor: pointer;" onclick="sortDividends('symbol')">SERIES <span id="sort-icon-symbol"></span></th>
                                    <th>FACE VALUE</th>
                                    <th>PURPOSE</th>
                                    <th style="cursor: pointer;" onclick="sortDividends('ex_date')">EX-DATE <span id="sort-icon-ex_date">▼</span></th>
                                    <th>RECORD DATE</th>
                                    <th>BOARD MEETING DATE</th>
                                    <th>AGM/EGM DATE</th>
                                </tr>
                            </thead>"""

content = content.replace(old_headers, new_headers)

with open(file_path, 'w') as f:
    f.write(content)

print("Updated table headers.")
