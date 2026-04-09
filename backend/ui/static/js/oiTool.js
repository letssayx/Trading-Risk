const OiTool = {
    active: false,
    containerId: 'oi-tool-container',
    allData: [],

    init: function(event, forceCompute = false) {
        const container = document.getElementById(this.containerId);
        if (container && !container.innerHTML.includes('oi-symbol')) {
            this.render(container);
            this.loadAggregatedData(forceCompute);
        } else if (forceCompute) {
            this.loadAggregatedData(true);
        }

        // Add enter key support
        const input = document.getElementById('oi-symbol');
        if (input) {
            if (typeof setupAutocomplete === 'function') {
                setupAutocomplete('oi-symbol');
            }
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    if (input.value.trim() === '') {
                        OiTool.loadAggregatedData();
                    } else {
                        OiTool.analyzeSingle();
                    }
                }
            });
            input.addEventListener('input', (e) => {
                if (input.value.trim() === '') {
                    OiTool.loadAggregatedData();
                } else {
                    if (document.getElementById('oi-analysis-body')) {
                        OiTool.filterData();
                    }
                }
            });
        }
    },

    render: function(container) {
        const html = `
            <div style="background: #1e1e1e; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 20px;">
                <div style="display: flex; gap: 15px; align-items: center; flex-wrap: wrap;">
                    <input type="text" id="oi-symbol" class="form-control history-input" placeholder="Search Symbol" style="width: 120px; padding: 4px;" oninput="OiTool.filterData()">
                    <select id="oi-sector-filter" class="form-control history-input" style="width: 130px; padding: 4px;" onchange="OiTool.filterData()">
                        <option value="">All Sectors</option>
                        <!-- Populated dynamically -->
                    </select>

                    <!-- Advanced Filters -->
                    <select id="oi-advanced-filter" class="form-control history-input" style="width: 180px; padding: 4px;" onchange="OiTool.filterData()">
                        <option value="">No Filter</option>
                        <option value="top_5_oi_add">Top 5 OI Additions</option>
                        <option value="top_10_oi_add">Top 10 OI Additions</option>
                        <option value="top_5_oi_red">Top 5 OI Reductions</option>
                        <option value="top_10_oi_red">Top 10 OI Reductions</option>
                        <option value="highest_oi_chg_30">Highest OI Chg (30 Days)</option>
                    </select>

                    <button id="oi-refresh-btn" onclick="OiTool.init(event, true)" class="btn btn-primary"><i class="fas fa-sync"></i> Refresh All</button>
                    <button onclick="OiTool.analyzeSingle()" class="btn btn-secondary">Load Single Symbol History</button>
                </div>
            </div>

            <!-- Dashboard Layout: 1/3 Chart, 2/3 Table -->
            <div style="display: flex; gap: 20px; flex-wrap: wrap; height: 100%;">
                <!-- Left: Quadrant Scatter Plot -->
                <div style="flex: 1; min-width: 300px; background: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 15px;">
                    <h4 style="margin-top: 0; color: #ccc; font-size: 14px;">Price vs OI Quadrant Analysis (1D)</h4>
                    <div id="oi-quadrant-chart" style="width: 100%; height: 400px; background: #151515;"></div>
                </div>

                <!-- Right: Aggregated Data Table -->
                <div style="flex: 2; min-width: 600px; background: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 15px; display: flex; flex-direction: column;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #ccc; font-size: 14px;">Aggregated Real-time OI Analysis <span id="oi-table-date" style="color: #888; font-size: 12px; margin-left: 10px;"></span></h4>
                        <div>
                            <button class="btn btn-secondary" onclick="OiTool.exportScatterCSV()"><i class="fas fa-download"></i> CSV</button>
                        </div>
                    </div>

                    <div style="flex: 1; overflow-y: auto;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 0.85em; text-align: left;">
                            <thead style="position: sticky; top: 0; background: #222; z-index: 10;">
                                <tr style="border-bottom: 2px solid #444; color: #888;">
                                    <th style="padding: 8px; width: 30px;"></th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('symbol')">Symbol ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('sector')">Sector ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('price')">FUT Price ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('price_chg_pct')">Price Chg % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('fut_oi')">FUT OI ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('fut_oi_chg')">FUT OI Chg ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('fut_oi_chg_pct')">FUT OI Chg % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('call_oi')">Call OI ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('call_oi_chg')">Call OI Chg ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('call_oi_chg_pct')">Call OI Chg % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('put_oi')">Put OI ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('put_oi_chg')">Put OI Chg ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('put_oi_chg_pct')">Put OI Chg % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('total_oi')">Total OI ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('pcr')">PCR ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('atm_iv')">ATM IV ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="OiTool.sortData('interpretation')">Quadrant ↕</th>
                                </tr>
                            </thead>
                            <tbody id="oi-analysis-body" style="color: #ccc;">
                                <tr><td colspan="18" style="text-align:center; padding: 20px;">Waiting for data...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        container.innerHTML = html;
    },

    loadAggregatedData: async function(forceCompute = false) {
        const tbody = document.getElementById('oi-analysis-body');
        const chartArea = document.getElementById('oi-quadrant-chart');
        if (!tbody) return;

        let eventSource = document.getElementById('oi-refresh-btn');
        let originalText = '';

        if (eventSource && forceCompute) {
            originalText = eventSource.innerHTML;
            eventSource.innerHTML = "<i class='fas fa-spinner fa-spin'></i> Computing Backend...";
            eventSource.disabled = true;
        }

        tbody.innerHTML = '<tr><td colspan="18" style="text-align:center; color:#888;">Fetching aggregated F&O data...</td></tr>';

        try {
            if (forceCompute) {
                const computeRes = await fetch('/api/data/analysis/oi/compute', { method: 'POST' });
                if (!computeRes.ok) throw new Error("Failed to compute OI analysis on backend.");
                // Ensure data takes half a second to settle and show success visually on the button before flashing
                await new Promise(r => setTimeout(r, 500));
            }

            const res = await fetch('/api/data/analysis/oi');
            if (!res.ok) throw new Error("Failed to load aggregated OI analysis.");
            const json = await res.json();

            if (json.date) {
                document.getElementById('oi-table-date').innerText = `(${json.date})`;
            }

            // Derive Quadrant explicitly for Scatter Plot
            this.allData = (json.data || []).map(d => {
                let interp = "Neutral";
                let p = d.price_chg_pct;
                let o = d.fut_oi_chg_pct;

                if (p > 0 && o > 0) interp = "Long Build Up";
                else if (p < 0 && o > 0) interp = "Short Build Up";
                else if (p > 0 && o < 0) interp = "Short Covering";
                else if (p < 0 && o < 0) interp = "Long Unwinding";

                d.interpretation = interp;
                return d;
            });

            this.populateSectors(this.allData);
            this.filterData(); // Applies any existing filters and calls renderData

        } catch(e) {
            tbody.innerHTML = `<tr><td colspan="18" style="text-align:center; color:red;">Error: ${e.message}</td></tr>`;
            chartArea.innerHTML = `<p style="color: red; padding: 20px;">Error: ${e.message}</p>`;
        } finally {
            if (eventSource && forceCompute) {
                eventSource.innerHTML = originalText;
                eventSource.disabled = false;
            }
        }
    },

    populateSectors: function(data) {
        const select = document.getElementById('oi-sector-filter');
        if (!select) return;

        const currentVal = select.value;
        const sectors = [...new Set(data.map(d => d.sector).filter(s => s && s !== 'Unknown'))].sort();

        let html = '<option value="">All Sectors</option>';
        sectors.forEach(s => {
            html += `<option value="${s}">${s}</option>`;
        });

        select.innerHTML = html;
        select.value = currentVal;
    },

    filterData: function() {
        const symbolTerm = document.getElementById('oi-symbol')?.value.toUpperCase() || '';
        const sectorTerm = document.getElementById('oi-sector-filter')?.value || '';
        const advFilter = document.getElementById('oi-advanced-filter')?.value || '';

        let filtered = this.allData;

        // 1. Text Filters
        if (symbolTerm) {
            filtered = filtered.filter(d => d.symbol.includes(symbolTerm));
        }
        if (sectorTerm) {
            filtered = filtered.filter(d => d.sector === sectorTerm);
        }

        // 2. Advanced Filters
        if (advFilter) {
            let sortedByOI = [...filtered].sort((a, b) => (b.fut_oi_chg_pct || 0) - (a.fut_oi_chg_pct || 0));

            if (advFilter === 'top_5_oi_add') filtered = sortedByOI.slice(0, 5);
            else if (advFilter === 'top_10_oi_add') filtered = sortedByOI.slice(0, 10);
            else if (advFilter === 'top_5_oi_red') filtered = sortedByOI.slice().reverse().slice(0, 5);
            else if (advFilter === 'top_10_oi_red') filtered = sortedByOI.slice().reverse().slice(0, 10);
            else if (advFilter.startsWith('highest_oi_chg_') || advFilter.startsWith('highest_price_chg_')) {
                // e.g., 'highest_oi_chg_30' maps to `d.fut_oi_chg_pct_30d` computed directly on backend
                const parts = advFilter.split('_');
                const days = parts[parts.length - 1]; // '30'
                const isPrice = advFilter.includes('price');
                const metricKey = isPrice ? `price_chg_pct_${days}d` : `fut_oi_chg_pct_${days}d`;

                // Sort by absolute highest magnitude of change and take top 15
                filtered = [...filtered].sort((a,b) => {
                    return Math.abs(b[metricKey] || 0) - Math.abs(a[metricKey] || 0);
                }).slice(0, 15);
            }
        }

        this.renderData(filtered);
    },

    renderData: function(displayData) {
        const tbody = document.getElementById('oi-analysis-body');
        if (!tbody) return;

        if (!displayData || displayData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="18" style="text-align:center; color:#888;">No F&O stocks found or no recent history. Please click Refresh All.</td></tr>';
            this.renderScatterPlot([]);
            return;
        }

        let html = '';
        displayData.forEach(d => {
            let color = '#aaa';
            if (d.interpretation === 'Long Build Up') color = '#00bcd4';   // Teal
            if (d.interpretation === 'Short Build Up') color = '#f44336';  // Red
            if (d.interpretation === 'Short Covering') color = '#4caf50';  // Green
            if (d.interpretation === 'Long Unwinding') color = '#ff9800'; // Orange

            let pColor = d.price_chg_pct >= 0 ? '#00bcd4' : '#f44336';
            let oColor = d.fut_oi_chg_pct >= 0 ? '#00bcd4' : '#f44336';
            let ceColor = d.call_oi_chg_pct >= 0 ? '#00bcd4' : '#f44336';
            let peColor = d.put_oi_chg_pct >= 0 ? '#00bcd4' : '#f44336';
            let oSign = d.fut_oi_chg >= 0 ? '+' : '';
            let ceSign = d.call_oi_chg >= 0 ? '+' : '';
            let peSign = d.put_oi_chg >= 0 ? '+' : '';

            html += `<tr class="oi-row" onclick="OiTool.toggleHistory('${d.symbol}')">
                <td style="padding: 8px; text-align: center; width: 30px;"><span id="oi-icon-${d.symbol}" style="font-size: 10px;">▶</span></td>
                <td style="padding: 8px; font-weight: bold; color: #fff;">${d.symbol}</td>
                <td style="padding: 8px; color: #aaa;">${d.sector || ''}</td>
                <td style="padding: 8px; color: #ffffff;">${(d.price || 0).toFixed(2)}</td>
                <td style="padding: 8px; color: ${pColor};">${(d.price_chg_pct || 0).toFixed(2)}%</td>
                <td style="padding: 8px;">${(d.fut_oi || 0).toLocaleString()}</td>
                <td style="padding: 8px; color: ${oColor};">${oSign}${(d.fut_oi_chg || 0).toLocaleString()}</td>
                <td style="padding: 8px; color: ${oColor};">${(d.fut_oi_chg_pct || 0).toFixed(2)}%</td>
                <td style="padding: 8px;">${(d.call_oi || 0).toLocaleString()}</td>
                <td style="padding: 8px; color: ${ceColor};">${ceSign}${(d.call_oi_chg || 0).toLocaleString()}</td>
                <td style="padding: 8px; color: ${ceColor};">${(d.call_oi_chg_pct || 0).toFixed(2)}%</td>
                <td style="padding: 8px;">${(d.put_oi || 0).toLocaleString()}</td>
                <td style="padding: 8px; color: ${peColor};">${peSign}${(d.put_oi_chg || 0).toLocaleString()}</td>
                <td style="padding: 8px; color: ${peColor};">${(d.put_oi_chg_pct || 0).toFixed(2)}%</td>
                <td style="padding: 8px;">${(d.total_oi || 0).toLocaleString()}</td>
                <td style="padding: 8px;">${d.pcr ? d.pcr.toFixed(2) : '-'}</td>
                <td style="padding: 8px;">${d.atm_iv ? d.atm_iv.toFixed(2) + '%' : '-'}</td>
                <td style="padding: 8px; color: ${color}; font-weight: bold;">${d.interpretation}</td>
            </tr>`;

            if (d.history && d.history.length > 1) {
                d.history.slice(1, 31).forEach(h => {
                    let hpColor = h.price_chg_pct >= 0 ? '#00bcd4' : '#f44336';
                    let hoColor = h.fut_oi_chg_pct >= 0 ? '#00bcd4' : '#f44336';
                    let hCeColor = h.call_oi_chg_pct >= 0 ? '#00bcd4' : '#f44336';
                    let hPeColor = h.put_oi_chg_pct >= 0 ? '#00bcd4' : '#f44336';

                    let hoSign = h.fut_oi_chg >= 0 ? '+' : '';
                    let hceSign = h.call_oi_chg >= 0 ? '+' : '';
                    let hpeSign = h.put_oi_chg >= 0 ? '+' : '';

                    // Matching exact columns
                    html += `<tr class="oi-history-row-${d.symbol}" style="background: #151515; border-bottom: 1px solid #222; font-size: 0.85em; display: none;">
                        <td style="padding: 6px 8px; width: 30px; border-right: 1px solid #333;"></td>
                        <td style="padding: 6px 8px;"></td>
                        <td style="padding: 6px 8px; color: #888;">└ ${h.date}</td>
                        <td style="padding: 6px 8px; color: #ccc;">${d.sector || '-'}</td>
                        <td style="padding: 6px 8px; color: #ffffff;">${(h.price || 0).toFixed(2)}</td>
                        <td style="padding: 6px 8px; color: ${hpColor}">${(h.price_chg_pct || 0).toFixed(2)}%</td>
                        <td style="padding: 6px 8px; color: #ccc;">${(h.fut_oi || 0).toLocaleString()}</td>
                        <td style="padding: 6px 8px; color: ${hoColor}">${hoSign}${(h.fut_oi_chg || 0).toLocaleString()}</td>
                        <td style="padding: 6px 8px; color: ${hoColor}">${(h.fut_oi_chg_pct || 0).toFixed(2)}%</td>
                        <td style="padding: 6px 8px; color: #ccc;">${(h.call_oi || 0).toLocaleString()}</td>
                        <td style="padding: 6px 8px; color: ${hCeColor}">${hceSign}${(h.call_oi_chg || 0).toLocaleString()}</td>
                        <td style="padding: 6px 8px; color: ${hCeColor}">${(h.call_oi_chg_pct || 0).toFixed(2)}%</td>
                        <td style="padding: 6px 8px; color: #ccc;">${(h.put_oi || 0).toLocaleString()}</td>
                        <td style="padding: 6px 8px; color: ${hPeColor}">${hpeSign}${(h.put_oi_chg || 0).toLocaleString()}</td>
                        <td style="padding: 6px 8px; color: ${hPeColor}">${(h.put_oi_chg_pct || 0).toFixed(2)}%</td>
                        <td style="padding: 6px 8px; color: #ccc;">${(h.total_oi || 0).toLocaleString()}</td>
                        <td style="padding: 6px 8px; color: #ccc;">${(h.pcr || 0).toFixed(2)}</td>
                        <td style="padding: 6px 8px; color: #ccc;">${(h.atm_iv || 0).toFixed(2)}</td>
                        <td style="padding: 6px 8px;"></td>
                    </tr>`;
                });
            }
        });

        tbody.innerHTML = html;

        // Render Scatter Plot
        this.renderScatterPlot(displayData);
    },

    toggleHistory: function(symbol) {
        const rows = document.querySelectorAll(`.oi-history-row-${symbol}`);
        const icon = document.getElementById(`oi-icon-${symbol}`);
        let isExpanded = false;
        rows.forEach(r => {
            if (r.style.display === 'none') {
                r.style.display = 'table-row';
                isExpanded = true;
            } else {
                r.style.display = 'none';
            }
        });
        if (icon) {
            icon.innerText = isExpanded ? '▼' : '▶';
        }
    },

    currentSortCol: '',
    currentSortDir: 'desc',

    sortData: function(col) {
        if (this.currentSortCol === col) {
            this.currentSortDir = this.currentSortDir === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSortCol = col;
            this.currentSortDir = 'desc';
        }

        this.allData.sort((a, b) => {
            let valA = a[col] || 0;
            let valB = b[col] || 0;

            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();

            if (valA < valB) return this.currentSortDir === 'asc' ? -1 : 1;
            if (valA > valB) return this.currentSortDir === 'asc' ? 1 : -1;
            return 0;
        });

        this.filterData();
    },

    renderScatterPlot: function(data) {
        const container = document.getElementById('oi-quadrant-chart');
        if (!container) return;

        if (data.length === 0) {
            container.innerHTML = '<p style="color:#888; text-align:center; padding-top: 50px;">No data</p>';
            return;
        }

        const validData = data.filter(d => d.price_chg_pct !== null && d.fut_oi_chg_pct !== null);

        let maxX = 0;
        let maxY = 0;
        validData.forEach(d => {
            if (Math.abs(d.price_chg_pct) > maxX) maxX = Math.abs(d.price_chg_pct);
            if (Math.abs(d.fut_oi_chg_pct) > maxY) maxY = Math.abs(d.fut_oi_chg_pct);
        });

        // Cap extreme outliers to prevent crazy squishing
        let zoomRangeX = Math.min(maxX * 1.1, 10); // cap max X to +/- 10%
        let zoomRangeY = Math.min(maxY * 1.1, 40); // cap max Y to +/- 40%

        const trace = {
            x: validData.map(d => d.price_chg_pct),
            y: validData.map(d => d.fut_oi_chg_pct),
            mode: 'markers+text',
            type: 'scatter',
            text: validData.map(d => d.symbol),
            textposition: 'top center',
            textfont: {
                family: 'monospace',
                size: 10,
                color: '#fff'
            },
            marker: {
                size: 8,
                color: validData.map(d => {
                    if (d.interpretation === 'Long Build Up') return '#00bcd4';
                    if (d.interpretation === 'Short Build Up') return '#f44336';
                    if (d.interpretation === 'Short Covering') return '#4caf50';
                    return '#ff9800'; // Long unwinding
                }),
                opacity: 0.8,
                line: { color: '#000', width: 1 }
            },
            hovertemplate:
                '<b>%{text}</b><br>' +
                'Price Chg: %{x:.2f}%<br>' +
                'OI Chg: %{y:.2f}%<extra></extra>'
        };

        const layout = {
            plot_bgcolor: 'transparent',
            paper_bgcolor: 'transparent',
            margin: { t: 20, r: 20, l: 40, b: 40 },
            xaxis: {
                title: 'Price Change %',
                color: '#aaa',
                zeroline: true,
                zerolinewidth: 2,
                zerolinecolor: '#ccc',
                gridcolor: '#333',
                range: [-zoomRangeX, zoomRangeX]
            },
            yaxis: {
                title: 'OI Change %',
                color: '#aaa',
                zeroline: true,
                zerolinewidth: 2,
                zerolinecolor: '#ccc',
                gridcolor: '#333',
                range: [-zoomRangeY, zoomRangeY],
                scaleanchor: 'x',
                scaleratio: zoomRangeY / (zoomRangeX === 0 ? 1 : zoomRangeX)
            },
            annotations: [
                { x: 0.05, y: 0.95, xref: 'paper', yref: 'paper', text: 'Short Covering', showarrow: false, font: {color: '#00bcd4', size: 16} },
                { x: 0.95, y: 0.95, xref: 'paper', yref: 'paper', text: 'Long Build Up', showarrow: false, font: {color: '#4caf50', size: 16} },
                { x: 0.05, y: 0.05, xref: 'paper', yref: 'paper', text: 'Long Unwinding', showarrow: false, font: {color: '#ff9800', size: 16} },
                { x: 0.95, y: 0.05, xref: 'paper', yref: 'paper', text: 'Short Build Up', showarrow: false, font: {color: '#f44336', size: 16} }
            ],
            dragmode: 'zoom'
        };

        const config = {
            responsive: true,
            scrollZoom: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d', 'pan2d']
        };

        Plotly.newPlot(container, [trace], layout, config);
    },

    exportScatterCSV: function() {
        const rows = [
            ['Symbol', 'Sector', 'FUT Price', 'Price Chg %', 'FUT OI', 'FUT OI Chg %', 'Call OI', 'Call OI Chg %', 'Put OI', 'Put OI Chg %', 'Total OI', 'PCR', 'ATM IV', 'Quadrant']
        ];

        this.allData.forEach(d => {
            rows.push([
                d.symbol,
                d.sector || '',
                d.price,
                d.price_chg_pct,
                d.fut_oi,
                d.fut_oi_chg_pct,
                d.call_oi,
                d.call_oi_chg_pct,
                d.put_oi,
                d.put_oi_chg_pct,
                d.total_oi,
                d.pcr,
                d.atm_iv,
                d.interpretation
            ]);
        });

        const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `oi_analysis_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
};

if (typeof window !== 'undefined') {
    if (!window.WorkbookManager) window.WorkbookManager = { modules: {} };
    if (!window.WorkbookManager.modules) window.WorkbookManager.modules = {};
    window.WorkbookManager.modules['oi'] = OiTool;
}
