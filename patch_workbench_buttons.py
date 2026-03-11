import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Add the Download Table button and Check Status back.
# Looking at where `mr-generate-btn` is
btn_search_str = """<button id="mr-generate-btn" class="btn btn-primary" style="margin-left: auto;" disabled>2. Generate PDF Report</button>"""
new_btn_str = """<button id="mr-generate-btn" class="btn btn-primary" style="margin-left: auto;" disabled>2. Generate PDF Report</button>
                    <button id="mr-status-btn" class="btn btn-secondary" style="margin-left: 10px;">Check Status</button>
                    <button id="mr-export-btn" class="btn btn-secondary" style="margin-left: 10px;">Download Table (CSV)</button>"""

if btn_search_str in content:
    content = content.replace(btn_search_str, new_btn_str)
else:
    # try another format
    print("Could not find exact button string, trying regex...")
    content = re.sub(r'<button id="mr-generate-btn"[^>]*>2\. Generate PDF Report</button>', new_btn_str, content)


# Add the export table logic back
export_logic = """
                // --- CSV Export Logic ---
                document.getElementById('mr-export-btn').addEventListener('click', () => {
                    const thead = document.getElementById('mr-data-head');
                    const tbody = document.getElementById('mr-data-body');
                    const statusText = document.getElementById('mr-status-text');
                    const originalText = statusText.innerText;

                    statusText.innerText = '⏳ Downloading CSV...';

                    setTimeout(() => {
                        try {
                            let csv = [];
                            const headRow = thead.querySelectorAll('tr th');
                            let headers = [];
                            headRow.forEach(h => {
                                // replace br and \n with space
                                headers.push('"' + h.innerText.replace(/\\n/g, ' ').replace(/\\r/g, '').trim() + '"');
                            });
                            csv.push(headers.join(','));

                            const rows = tbody.querySelectorAll('tr');
                            rows.forEach(r => {
                                let rowData = [];
                                r.querySelectorAll('td').forEach(c => {
                                    rowData.push('"' + c.innerText.trim() + '"');
                                });
                                csv.push(rowData.join(','));
                            });

                            const csvString = csv.join('\\n');
                            const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
                            const url = URL.createObjectURL(blob);
                            const link = document.createElement('a');
                            link.setAttribute('href', url);

                            const targetDate = document.getElementById('mr-target-date').value;
                            const symbol = document.getElementById('mr-symbol-input').value || 'NIFTY';
                            const isSnapshot = !document.getElementById('mr-symbol-input').parentElement.style.display || document.getElementById('mr-symbol-input').parentElement.style.display === 'none';

                            const filename = isSnapshot ? `derivatives_snapshot_${targetDate}.csv` : `derivatives_timeseries_${symbol}.csv`;

                            link.setAttribute('download', filename);
                            link.style.display = 'none';
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                            statusText.innerText = originalText;
                        } catch(e) {
                            statusText.innerText = `CSV Error: ${e.message}`;
                        }
                    }, 50);
                });

                // Status Check Button Logic
                document.getElementById('mr-status-btn').addEventListener('click', async () => {
                    const targetDate = document.getElementById('mr-target-date').value;
                    if(!targetDate) { alert('Please select a date.'); return; }
                    const statusText = document.getElementById('mr-status-text');

                    try {
                        const res = await fetch(`/api/morning-report/data/${targetDate}`);
                        if(res.ok) {
                            const data = await res.json();
                            if(data && data.length > 0) {
                                statusText.innerText = `Status: Data Ready (${data.length} records available).`;
                                statusText.style.color = '#4CAF50';
                                loadTimeseriesData(true);
                            } else {
                                statusText.innerText = 'Status: Data Not Prepared yet.';
                                statusText.style.color = '#ff9800';
                            }
                        }
                    } catch (e) {
                        statusText.innerText = `Status Error: ${e.message}`;
                    }
                });
"""

# Inject script logic before the end of the script tag for derivatives
script_insertion_point = content.find("document.getElementById('mr-fetch-ts-btn').addEventListener('click', () => loadTimeseriesData(false));")
if script_insertion_point != -1:
    content = content[:script_insertion_point] + export_logic + "\n" + content[script_insertion_point:]

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
