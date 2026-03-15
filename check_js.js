                document.getElementById('mr-target-date').valueAsDate = new Date();
                let mrPollingInterval;

                // Load Archive
                async function loadMrArchive() {
                    const list = document.getElementById('mr-archive-list');
                    try {
                        const res = await fetch('/api/morning-report/list');
                        const data = await res.json();
                        if (data.reports.length === 0) {
                            list.innerHTML = '<li style="color: #666; font-style: italic;">No reports found.</li>';
                            return;
                        }
                        list.innerHTML = '';
                        data.reports.forEach(r => {
                            const li = document.createElement('li');
                            li.style.marginBottom = '8px';
                            li.innerHTML = `<a href="${r.url}" target="_blank" style="color: #4da6ff; text-decoration: none;">📄 ${r.date}</a>`;
                            list.appendChild(li);
                        });
                    } catch (e) {
                        list.innerHTML = '<li style="color: red;">Failed to load.</li>';
                    }
                }

                // Initialize archive list
                loadMrArchive();

                // Prepare Data Button Handler
                document.getElementById('mr-prepare-btn').addEventListener('click', async () => {
                    const targetDate = document.getElementById('mr-target-date').value;
                    const endDate = document.getElementById('mr-end-date').value;
                    const statusText = document.getElementById('mr-status-text');
                    const prepBtn = document.getElementById('mr-prepare-btn');
                    const genBtn = document.getElementById('mr-generate-btn');
                    const tbody = document.getElementById('mr-data-body');

                    if(!targetDate) { alert('Please select a From Date.'); return; }

                    prepBtn.disabled = true;
                    prepBtn.style.opacity = '0.5';
                    statusText.innerText = endDate ? 'Triggering historical range preparation task (this may take a while)...' : 'Triggering data preparation task...';
                    statusText.style.color = '#aaa';
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #888; padding: 20px;">Calculating composite metrics...</td></tr>';

                    try {
                        const res = await fetch('/api/morning-report/prepare', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ target_date: targetDate, end_date: endDate || null })
                        });
                        const data = await res.json();

                        if(data.task_id) {
                            statusText.innerText = 'Processing metrics...';
                            mrPollingInterval = setInterval(() => checkPrepStatus(data.task_id, targetDate), 3000);
                        } else {
                            throw new Error('No task ID returned.');
                        }
                    } catch (e) {
                        statusText.innerText = `Error: ${e.message}`;
                        statusText.style.color = 'red';
                        prepBtn.disabled = false;
                        prepBtn.style.opacity = '1';
                    }
                });

                async function checkPrepStatus(taskId, targetDate) {
                    try {
                        const res = await fetch(`/api/morning-report/status/${taskId}`);
                        const data = await res.json();
                        const statusText = document.getElementById('mr-status-text');
                        const genBtn = document.getElementById('mr-generate-btn');
                        const prepBtn = document.getElementById('mr-prepare-btn');

                        if(data.state === 'SUCCESS' || data.status === 'SUCCESS') {
                            clearInterval(mrPollingInterval);
                            statusText.innerText = 'Data Prepared Successfully.';
                            statusText.style.color = '#28a745';

                            prepBtn.disabled = false;
                            prepBtn.style.opacity = '1';
                            genBtn.disabled = false;
                            genBtn.style.opacity = '1';

                            // Auto-load data
                            loadTimeseriesData(true);
                        } else if(data.state === 'FAILURE' || data.status === 'FAILED' || data.status === 'FAILURE') {
                            clearInterval(mrPollingInterval);
                            statusText.innerText = `Preparation Failed: ${data.error || 'Unknown Error'}`;
                            statusText.style.color = 'red';
                            prepBtn.disabled = false;
                            prepBtn.style.opacity = '1';
                        }
                    } catch (e) {
                        console.error('Error polling prep status', e);
                    }
                }

                // View Data Button Handler (Timeseries / Snapshot)
                const generateTableHTML = (row, isSnapshot) => {
                            const close = (row.close_price != null && !isNaN(Number(row.close_price))) ? Number(row.close_price).toFixed(2) : '-';
                            const vwap = (row.vwap != null && !isNaN(Number(row.vwap))) ? Number(row.vwap).toFixed(2) : '-';
                            const fVol = (row.futures_total_vol != null && !isNaN(Number(row.futures_total_vol))) ? Number(row.futures_total_vol).toLocaleString() : '-';
                            const fOi = (row.futures_total_oi != null && !isNaN(Number(row.futures_total_oi))) ? Number(row.futures_total_oi).toLocaleString() : '-';
                            const pcr = (row.pcr_oi != null && !isNaN(Number(row.pcr_oi))) ? Number(row.pcr_oi).toFixed(2) : '-';

                            const hiOiStrikePe = (row.highest_oi_strike_pe != null && !isNaN(Number(row.highest_oi_strike_pe))) ? Number(row.highest_oi_strike_pe).toLocaleString() : '-';
                            const pctAwayPe = (row.pct_away_highest_pe != null && !isNaN(Number(row.pct_away_highest_pe))) ? (Number(row.pct_away_highest_pe)).toFixed(2) + '%' : '-';
                            const hiOiStrikeCe = (row.highest_oi_strike_ce != null && !isNaN(Number(row.highest_oi_strike_ce))) ? Number(row.highest_oi_strike_ce).toLocaleString() : '-';
                            const pctAwayCe = (row.pct_away_highest_ce != null && !isNaN(Number(row.pct_away_highest_ce))) ? (Number(row.pct_away_highest_ce)).toFixed(2) + '%' : '-';
                            const chgOiOpt = (row.chg_oi_options != null && !isNaN(Number(row.chg_oi_options))) ? Number(row.chg_oi_options).toLocaleString() : '-';
                            const chgOiFut = (row.chg_oi_futures != null && !isNaN(Number(row.chg_oi_futures))) ? Number(row.chg_oi_futures).toLocaleString() : '-';
                            const fut1Exp = row.near_expiry_date !== null ? row.near_expiry_date : '-';
                            const fut2Exp = row.next_expiry_date !== null ? row.next_expiry_date : '-';
                            const fut3Exp = row.far_expiry_date !== null ? row.far_expiry_date : '-';
                            const totCallOi = (row.total_options_call_oi != null && !isNaN(Number(row.total_options_call_oi))) ? Number(row.total_options_call_oi).toLocaleString() : '-';
                            const totPutOi = (row.total_options_put_oi != null && !isNaN(Number(row.total_options_put_oi))) ? Number(row.total_options_put_oi).toLocaleString() : '-';

                            const atmIvNear = (row.atm_iv_near != null && !isNaN(Number(row.atm_iv_near))) ? (Number(row.atm_iv_near) * 100).toFixed(2) + '%' : '-';
                            const atmIvNext = (row.atm_iv_next != null && !isNaN(Number(row.atm_iv_next))) ? (Number(row.atm_iv_next) * 100).toFixed(2) + '%' : '-';
                            const ivRank = (row.iv_rank_252 != null && !isNaN(Number(row.iv_rank_252))) ? Number(row.iv_rank_252).toFixed(2) : '-';
                            const ivPctile = (row.iv_percentile_252 != null && !isNaN(Number(row.iv_percentile_252))) ? Number(row.iv_percentile_252).toFixed(2) : '-';
                            const skewNear = (row.skew_25d_near != null && !isNaN(Number(row.skew_25d_near))) ? (Number(row.skew_25d_near) * 100).toFixed(2) + '%' : '-';
                            const skewFar = (row.skew_25d_far != null && !isNaN(Number(row.skew_25d_far))) ? (Number(row.skew_25d_far) * 100).toFixed(2) + '%' : '-';
                            const vol1Sig = (row.daily_volatility != null && !isNaN(Number(row.daily_volatility))) ? (Number(row.daily_volatility) * 100).toFixed(2) + '%' : '-';

                            const roll = (row.rollover_pct != null && !isNaN(Number(row.rollover_pct))) ? (Number(row.rollover_pct) * 100).toFixed(2) + '%' : '-';

                            let mwpl = '0.00';
                            let maxMwpl = 0;
                            let maxClient = '';
                            if (row.mwpl_array && Array.isArray(row.mwpl_array) && row.mwpl_array.length > 0) {
                                // mwpl_array is usually [{"client_name": value}, ...] or [value] or string.
                                // To be safe, we extract the highest value if it's an array of objects.
                                try {
                                    row.mwpl_array.forEach(item => {
                                        if (typeof item === 'object' && item !== null) {
                                            for (let key in item) {
                                                const val = parseFloat(item[key]);
                                                if (!isNaN(val) && val > maxMwpl) {
                                                    maxMwpl = val;
                                                    maxClient = key;
                                                }
                                            }
                                        } else if (typeof item === 'number') {
                                            if (item > maxMwpl) maxMwpl = item;
                                        }
                                    });
                                    if (maxMwpl > 0) {
                                        mwpl = maxMwpl.toFixed(2);
                                    } else {
                                        // fallback if structure was different
                                        const firstKey = Object.keys(row.mwpl_array[0])[0];
                                        if (firstKey) mwpl = parseFloat(row.mwpl_array[0][firstKey]).toFixed(2);
                                    }
                                } catch (e) {
                                    mwpl = '0.00';
                                }
                            }

                            const basis1 = (row.basis_1_bps != null && !isNaN(Number(row.basis_1_bps))) ? Number(row.basis_1_bps).toFixed(0) : '-';
                            const basis2 = (row.basis_2_bps != null && !isNaN(Number(row.basis_2_bps))) ? Number(row.basis_2_bps).toFixed(0) : '-';
                            const cal1 = (row.calendar_spread_1_bps != null && !isNaN(Number(row.calendar_spread_1_bps))) ? Number(row.calendar_spread_1_bps).toFixed(0) : '-';
                            const cal2 = (row.calendar_spread_2_bps != null && !isNaN(Number(row.calendar_spread_2_bps))) ? Number(row.calendar_spread_2_bps).toFixed(0) : '-';

                            const pe = (row.pe_ratio != null && !isNaN(Number(row.pe_ratio))) ? Number(row.pe_ratio).toFixed(2) : '-';
                            const b252 = (row.beta_252 != null && !isNaN(Number(row.beta_252))) ? Number(row.beta_252).toFixed(2) : '-';
                            const b500 = (row.beta_500 != null && !isNaN(Number(row.beta_500))) ? Number(row.beta_500).toFixed(2) : '-';
                            const r252 = (row.r_squared_252 != null && !isNaN(Number(row.r_squared_252))) ? Number(row.r_squared_252).toFixed(2) : '-';
                            const r500 = (row.r_squared_500 != null && !isNaN(Number(row.r_squared_500))) ? Number(row.r_squared_500).toFixed(2) : '-';
                            const pxPct = (row.price_pct_change != null && !isNaN(Number(row.price_pct_change))) ? (Number(row.price_pct_change)).toFixed(2) + '%' : '-';
                            const relVol = (row.relative_volume_20d != null && !isNaN(Number(row.relative_volume_20d))) ? Number(row.relative_volume_20d).toFixed(2) : '-';

                            const atr = (row.atr_14_cash != null && !isNaN(Number(row.atr_14_cash))) ? Number(row.atr_14_cash).toFixed(2) : '-';
                            const ema20 = (row.ema_20_cash != null && !isNaN(Number(row.ema_20_cash))) ? Number(row.ema_20_cash).toFixed(2) : '-';
                            const ema50 = (row.ema_50_cash != null && !isNaN(Number(row.ema_50_cash))) ? Number(row.ema_50_cash).toFixed(2) : '-';
                            const ema100 = (row.ema_100_cash != null && !isNaN(Number(row.ema_100_cash))) ? Number(row.ema_100_cash).toFixed(2) : '-';
                            const ema200 = (row.ema_200_cash != null && !isNaN(Number(row.ema_200_cash))) ? Number(row.ema_200_cash).toFixed(2) : '-';

                            // Note: delivery fields don't exist in model, using '-'
                            const del5 = '-';
                            const del10 = '-';
                            const del20 = '-';
                            const del30 = '-';

                            let html = ``;
                            if(!isSnapshot) {
                                html += `<td style="position: sticky; left: 0; background: #1e1e1e; z-index: 2;">${row.trade_date}</td>`;
                                html += `<td style="position: sticky; left: 90px; background: #1e1e1e; z-index: 2;">${row.symbol}</td>`;
                            } else {
                                html += `<td style="position: sticky; left: 0; background: #1e1e1e; z-index: 2;">${row.symbol}</td>`;
                            }

                            html += `
                                <td>${close}</td>
                                <td>${vwap}</td>
                                <td>${fVol}</td>
                                <td>${fOi}</td>
                                <td>${pcr}</td>
                                <td>${hiOiStrikePe}</td>
                                <td>${pctAwayPe}</td>
                                <td>${hiOiStrikeCe}</td>
                                <td>${pctAwayCe}</td>
                                <td>${chgOiOpt}</td>
                                <td>${chgOiFut}</td>
                                <td>${fut1Exp}</td>
                                <td>${fut2Exp}</td>
                                <td>${fut3Exp}</td>
                                <td>${totCallOi}</td>
                                <td>${totPutOi}</td>
                                <td>${atmIvNear}</td>
                                <td>${atmIvNext}</td>
                                <td>${ivRank}</td>
                                <td>${ivPctile}</td>
                                <td>${skewNear}</td>
                                <td>${skewFar}</td>
                                <td>${vol1Sig}</td>
                                <td>${roll}</td>
                                <td style="color: ${parseFloat(mwpl) > 20 ? '#ff4d4d' : 'inherit'};">${mwpl}</td>
                                <td>${basis1}</td>
                                <td>${basis2}</td>
                                <td>${cal1}</td>
                                <td>${cal2}</td>
                                <td>${pe}</td>
                                <td>${b252}</td>
                                <td>${b500}</td>
                                <td>${r252}</td>
                                <td>${r500}</td>
                                <td>${pxPct}</td>
                                <td>${relVol}</td>
                                <td>${atr}</td>
                                <td>${ema20}</td>
                                <td>${ema50}</td>
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
