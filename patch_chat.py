import sys
import re

def patch_file(file_path):
    with open(file_path, "r") as f:
        content = f.read()

    # Find the rendering logic for dividend_table
    if "if (w.widget === 'dividend_table') {" in content:
        # We need to modify the table generation inside the renderWidget logic to hide rows > 10
        pattern = r"(const tableBody = w\.data\.map\(\(row\) => \{\s*return \`<tr.*?>\s*.*?\s*</tr>\`\s*\}\)\.join\(''\);)"
        replacement = """
                let tableBody = '';
                const maxVisible = 10;
                w.data.forEach((row, idx) => {
                    const rowHtml = `<tr style="border-bottom: 1px solid #333; ${idx >= maxVisible ? 'display: none;' : ''}" class="data-row-${id}">
                        <td style="padding: 10px;">${row["Symbol"]}</td>
                        <td style="padding: 10px;">${row["Event Type"]}</td>
                        <td style="padding: 10px;">${row["Date / Ex-Date"]}</td>
                        <td style="padding: 10px; font-weight: bold; color: #4caf50;">${row["Amount"]}</td>
                        <td style="padding: 10px;">${row["Type"]}</td>
                        <td style="padding: 10px;">
                            <span style="background: ${row["Status"] === 'Awaited' ? '#ff9800' : '#4caf50'}20; color: ${row["Status"] === 'Awaited' ? '#ff9800' : '#4caf50'}; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                                ${row["Status"]}
                            </span>
                        </td>
                        <td style="padding: 10px; max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${row["Details"]}">${row["Details"]}</td>
                    </tr>`;
                    tableBody += rowHtml;
                });

                let showMoreBtn = '';
                if (w.data.length > maxVisible) {
                    showMoreBtn = `<div style="text-align: center; margin-top: 10px;">
                        <button onclick="toggleRows('${id}')" style="background: #2d3748; color: #fff; border: 1px solid #4a5568; padding: 5px 15px; border-radius: 15px; cursor: pointer; font-size: 12px;">Show More (${w.data.length - maxVisible})</button>
                    </div>`;
                }
        """

        # We also need to add a global script for toggleRows
        script_addition = """
        <script>
            function toggleRows(id) {
                const rows = document.querySelectorAll(`.data-row-${id}`);
                let isHidden = false;
                rows.forEach((r, idx) => {
                    if (idx >= 10) {
                        if (r.style.display === 'none') {
                            r.style.display = 'table-row';
                            isHidden = true;
                        } else {
                            r.style.display = 'none';
                        }
                    }
                });

                const btn = event.target;
                if (isHidden) {
                    btn.innerText = 'Show Less';
                } else {
                    btn.innerText = `Show More (${rows.length - 10})`;
                }
            }
        </script>
        """

        print("Will apply JS patch.")

    else:
        print("Did not find dividend_table render block")

patch_file("backend/ui/templates/chat.html")
