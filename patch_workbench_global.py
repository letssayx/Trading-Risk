import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Found the bug: my regex extraction left a piece of the return statement dangling inside the `loadTimeseriesData` function due to multiple template literals.
# Let's fix this properly. I will replace the broken `loadTimeseriesData` entirely.

start_load = content.find("async function loadTimeseriesData(snapshotMode = true) {")
end_load = content.find("document.getElementById('mr-fetch-ts-btn').addEventListener('click', () => loadTimeseriesData(false));")

if start_load == -1 or end_load == -1:
    print("Could not find loadTimeseriesData bounds")
    exit(1)

new_load = """async function loadTimeseriesData(snapshotMode = true) {
                    const targetDate = document.getElementById('mr-target-date').value;
                    const symbol = document.getElementById('mr-symbol-input').value.toUpperCase() || 'NIFTY';
                    const tbody = document.getElementById('mr-data-body');
                    const thead = document.getElementById('mr-data-head');
                    const statusText = document.getElementById('mr-status-text');

                    if(snapshotMode && !targetDate) return;
                    if(!snapshotMode && !symbol) { alert('Please enter a symbol for Timeseries view.'); return; }

                    try {
                        let url = `/api/morning-report/data/${targetDate}`;
                        if (!snapshotMode) {
                            url = `/api/morning-report/timeseries?symbol=${symbol}`;
                        }

                        const res = await fetch(url);
                        if (!res.ok) throw new Error('Data fetch failed');
                        const data = await res.json();

                        tbody.innerHTML = '';
                        if(data.length === 0) {
                            tbody.innerHTML = `<tr><td colspan="${snapshotMode ? 41 : 42}" style="text-align: center; color: #888; padding: 20px;">No data found.</td></tr>`;
                            return;
                        }

                        if (snapshotMode) {
                            thead.innerHTML = `
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3;">Symbol</th>
                                    <th style="white-space: pre-wrap;">Close<br>Price</th>
                                    <th style="white-space: pre-wrap;">VWAP</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total Vol</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total OI</th>
                                    <th style="white-space: pre-wrap;">Put-Call<br>Ratio (OI)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (PE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (CE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(CE)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Options)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Futures)</th>
                                    <th style="white-space: pre-wrap;">Fut 1<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 2<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 3<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Call OI</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Put OI</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Next)</th>
                                    <th style="white-space: pre-wrap;">IV Rank<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">IV Percentile<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Far)</th>
                                    <th style="white-space: pre-wrap;">1-Sigma Daily<br>Volatility</th>
                                    <th style="white-space: pre-wrap;">Rollover<br>Percentage</th>
                                    <th style="white-space: pre-wrap;">MWPL %<br>(Top Client)</th>
                                    <th style="white-space: pre-wrap;">Basis 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Basis 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">P/E<br>Ratio</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">Price %<br>Change</th>
                                    <th style="white-space: pre-wrap;">Relative Vol<br>(20d)</th>
                                    <th style="white-space: pre-wrap;">14-Day<br>ATR %</th>
                                    <th style="white-space: pre-wrap;">20-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">50-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">100-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">200-Day<br>EMA</th>
                                </tr>
                            `;
                            const renderChunk = (start) => {
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
                            requestAnimationFrame(() => renderChunk(0));
                        } else {
                            thead.innerHTML = `
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Date</th>
                                    <th style="text-align: left; position: sticky; top: 0; left: 90px; background: #1e1e1e; z-index: 3;">Symbol</th>
                                    <th style="white-space: pre-wrap;">Close<br>Price</th>
                                    <th style="white-space: pre-wrap;">VWAP</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total Vol</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total OI</th>
                                    <th style="white-space: pre-wrap;">Put-Call<br>Ratio (OI)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (PE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (CE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(CE)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Options)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Futures)</th>
                                    <th style="white-space: pre-wrap;">Fut 1<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 2<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 3<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Call OI</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Put OI</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Next)</th>
                                    <th style="white-space: pre-wrap;">IV Rank<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">IV Percentile<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Far)</th>
                                    <th style="white-space: pre-wrap;">1-Sigma Daily<br>Volatility</th>
                                    <th style="white-space: pre-wrap;">Rollover<br>Percentage</th>
                                    <th style="white-space: pre-wrap;">MWPL %<br>(Top Client)</th>
                                    <th style="white-space: pre-wrap;">Basis 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Basis 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">P/E<br>Ratio</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">Price %<br>Change</th>
                                    <th style="white-space: pre-wrap;">Relative Vol<br>(20d)</th>
                                    <th style="white-space: pre-wrap;">14-Day<br>ATR %</th>
                                    <th style="white-space: pre-wrap;">20-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">50-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">100-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">200-Day<br>EMA</th>
                                </tr>
                            `;
                            const renderChunk = (start) => {
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
                            requestAnimationFrame(() => renderChunk(0));
                        }
                    } catch(e) {
                        statusText.innerText = 'Failed to load data.';
                        tbody.innerHTML = `<tr><td colspan="42" style="text-align: center; color: red; padding: 20px;">${e.message}</td></tr>`;
                    }
                }
"""

content = content[:start_load] + new_load + "\n                " + content[end_load:]

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
