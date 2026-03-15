                                <td>${ema100}</td>
                                <td>${ema200}</td>
                            </tr>
                        \`;
                        return html;
                }

                async function loadTimeseriesData(snapshotMode = true) {
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
