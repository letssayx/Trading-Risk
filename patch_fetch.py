import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Make the loadTimeseriesData use chunks to not block the UI thread during rendering.
old_load_logic = """                        tbody.innerHTML = '';
                        if (data.length === 0) {
                            tbody.innerHTML = `<tr><td colspan="42" style="text-align: center; color: #aaa; padding: 20px;">No data found.</td></tr>`;
                            statusText.innerText = 'No records.';
                            return;
                        }"""

new_load_logic = """                        statusText.innerText = 'Rendering data...';
                        tbody.innerHTML = '';
                        if (data.length === 0) {
                            tbody.innerHTML = `<tr><td colspan="42" style="text-align: center; color: #aaa; padding: 20px;">No data found.</td></tr>`;
                            statusText.innerText = 'No records.';
                            return;
                        }"""

if old_load_logic in content:
    content = content.replace(old_load_logic, new_load_logic)

# Replace the blocking forEach with a chunked rendering or just add try/catch
old_data_render_snapshot = """                            data.forEach(row => {
                                const tr = document.createElement('tr');
                                tr.innerHTML = generateTableHTML(row, true);
                                tbody.appendChild(tr);
                            });"""
new_data_render_snapshot = """                            const renderChunk = (start) => {
                                const end = Math.min(start + 50, data.length);
                                const fragment = document.createDocumentFragment();
                                for (let i = start; i < end; i++) {
                                    const tr = document.createElement('tr');
                                    tr.innerHTML = generateTableHTML(data[i], true);
                                    fragment.appendChild(tr);
                                }
                                tbody.appendChild(fragment);
                                if (end < data.length) {
                                    requestAnimationFrame(() => renderChunk(end));
                                } else {
                                    statusText.innerText = `Loaded ${data.length} records.`;
                                    const genBtn = document.getElementById('mr-generate-btn');
                                    if(genBtn) { genBtn.disabled = false; genBtn.style.opacity = '1'; }
                                }
                            };
                            requestAnimationFrame(() => renderChunk(0));"""

content = content.replace(old_data_render_snapshot, new_data_render_snapshot)


old_data_render_ts = """                            data.forEach(row => {
                                const tr = document.createElement('tr');
                                tr.innerHTML = generateTableHTML(row, false);
                                tbody.appendChild(tr);
                            });"""

new_data_render_ts = """                            const renderChunk = (start) => {
                                const end = Math.min(start + 50, data.length);
                                const fragment = document.createDocumentFragment();
                                for (let i = start; i < end; i++) {
                                    const tr = document.createElement('tr');
                                    tr.innerHTML = generateTableHTML(data[i], false);
                                    fragment.appendChild(tr);
                                }
                                tbody.appendChild(fragment);
                                if (end < data.length) {
                                    requestAnimationFrame(() => renderChunk(end));
                                } else {
                                    statusText.innerText = `Loaded ${data.length} records.`;
                                }
                            };
                            requestAnimationFrame(() => renderChunk(0));"""

content = content.replace(old_data_render_ts, new_data_render_ts)

# Remove the synchronous status update since chunking handles it asynchronously
old_sync_status = """statusText.innerText = `Loaded ${data.length} records.`;

                        // Enable generate button if data exists (snapshot mode)
                        const genBtn = document.getElementById('mr-generate-btn');
                        genBtn.disabled = false;
                        genBtn.style.opacity = '1';"""

new_sync_status = """// Status updated async during renderChunk"""
content = content.replace(old_sync_status, new_sync_status)


with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
