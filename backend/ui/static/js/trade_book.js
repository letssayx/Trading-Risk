class TradeBook {
    constructor(containerId) {
        this.containerId = containerId;
        this.trades = [];
        this.filter = 'today'; // today, week, month, all

        // Mock Data for MVP
        this.trades = [
            { id: '#1024', time: '2023-10-27 10:45:00', symbol: 'NIFTY 24000 CE', side: 'BUY', qty: 500, entry: 145.50, exit: 152.00, pnl: 3250.00, strategy: 'Turtle', status: 'CLOSED' },
            { id: '#1023', time: '2023-10-27 10:42:11', symbol: 'BANKNIFTY FUT', side: 'SELL', qty: 30, entry: 44500, exit: 44480, pnl: 600.00, strategy: 'StatArb', status: 'CLOSED' },
            { id: '#1022', time: '2023-10-26 09:15:05', symbol: 'RELIANCE', side: 'BUY', qty: 100, entry: 2450, exit: 2440, pnl: -1000.00, strategy: 'Momentum', status: 'CLOSED' },
            { id: '#1021', time: '2023-10-25 14:30:00', symbol: 'TCS', side: 'BUY', qty: 50, entry: 3200, exit: 3210, pnl: 500.00, strategy: 'Value', status: 'CLOSED' },
            { id: '#1025', time: '2023-10-27 11:00:00', symbol: 'INFY', side: 'SELL', qty: 200, entry: 1400, exit: null, pnl: 150.00, strategy: 'Hedge', status: 'OPEN' }
        ];

        this.init();
    }

    init() {
        this.render();
        this.attachEvents();
    }

    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // Calculate Stats
        const filteredTrades = this.filterTrades(this.filter);
        const totalPnL = filteredTrades.reduce((acc, t) => acc + (t.pnl || 0), 0);
        const wins = filteredTrades.filter(t => t.pnl > 0).length;
        const winRate = filteredTrades.length > 0 ? ((wins / filteredTrades.length) * 100).toFixed(1) : 0;
        const openPos = this.trades.filter(t => t.status === 'OPEN').length;

        container.innerHTML = `
            <div class="panel-header">
                <div style="display:flex; gap:10px; align-items:center;">
                    <span>📊 Trade Book</span>
                    <div class="trade-filters">
                        <button class="filter-btn ${this.filter === 'today' ? 'active' : ''}" data-filter="today">Today</button>
                        <button class="filter-btn ${this.filter === 'week' ? 'active' : ''}" data-filter="week">Week</button>
                        <button class="filter-btn ${this.filter === 'month' ? 'active' : ''}" data-filter="month">Month</button>
                        <button class="filter-btn ${this.filter === 'all' ? 'active' : ''}" data-filter="all">All</button>
                    </div>
                </div>
                <div>
                     <span style="font-size:0.8em; margin-right:15px;">Open: ${openPos}</span>
                     <button class="key-btn" style="padding:2px 8px; font-size:0.75em;" id="export-btn">Export Excel</button>
                </div>
            </div>
            <div class="panel-content" style="display:flex; flex-direction:column; height:100%;">
                <div class="trade-table-container" style="flex:1; overflow:auto;">
                    <table class="trade-book-table" id="tradeBookTable">
                        <thead>
                            <tr>
                                <th onclick="tradeBook.sortTable(0)">ID<div class="column-resizer"></div></th>
                                <th onclick="tradeBook.sortTable(1)">Time<div class="column-resizer"></div></th>
                                <th onclick="tradeBook.sortTable(2)">Symbol<div class="column-resizer"></div></th>
                                <th onclick="tradeBook.sortTable(3)">Side<div class="column-resizer"></div></th>
                                <th onclick="tradeBook.sortTable(4)">Qty<div class="column-resizer"></div></th>
                                <th onclick="tradeBook.sortTable(5)">Entry<div class="column-resizer"></div></th>
                                <th onclick="tradeBook.sortTable(6)">Exit<div class="column-resizer"></div></th>
                                <th onclick="tradeBook.sortTable(7)">PnL<div class="column-resizer"></div></th>
                                <th onclick="tradeBook.sortTable(8)">Strategy<div class="column-resizer"></div></th>
                                <th onclick="tradeBook.sortTable(9)">Status<div class="column-resizer"></div></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.renderRows(filteredTrades)}
                        </tbody>
                    </table>
                </div>
                <div class="trade-summary" style="padding:5px 10px; background:#222; border-top:1px solid #333; font-size:0.85em; display:flex; gap:20px;">
                    <span>Total PnL: <span class="${totalPnL >= 0 ? 'val-green' : 'val-red'}">${totalPnL.toFixed(2)}</span></span>
                    <span>Win Rate: ${winRate}%</span>
                    <span>Trades: ${filteredTrades.length}</span>
                </div>
            </div>
        `;

        // Re-attach resizers since DOM changed
        this.initResizers();
    }

    renderRows(trades) {
        if (trades.length === 0) return '<tr><td colspan="10" style="text-align:center; padding:20px; color:#666;">No trades found</td></tr>';

        return trades.map(t => `
            <tr>
                <td>${t.id}</td>
                <td>${t.time.split(' ')[1]}</td> <!-- Show Time only -->
                <td>${t.symbol}</td>
                <td class="${t.side === 'BUY' ? 'val-green' : 'val-red'}" contenteditable="true" onblur="tradeBook.onCellEdit(this, '${t.id}', 'side')">${t.side}</td>
                <td contenteditable="true" onblur="tradeBook.onCellEdit(this, '${t.id}', 'qty')">${t.qty}</td>
                <td contenteditable="true" onblur="tradeBook.onCellEdit(this, '${t.id}', 'entry')">${t.entry}</td>
                <td contenteditable="true" onblur="tradeBook.onCellEdit(this, '${t.id}', 'exit')">${t.exit || '-'}</td>
                <td class="${t.pnl >= 0 ? 'val-green' : 'val-red'}">${t.pnl ? t.pnl.toFixed(2) : '-'}</td>
                <td>${t.strategy}</td>
                <td><span style="font-size:0.8em; padding:2px 4px; border-radius:2px; background:${t.status==='OPEN'?'#2196F3':'#444'}">${t.status}</span></td>
            </tr>
        `).join('');
    }

    attachEvents() {
        const container = document.getElementById(this.containerId);
        container.addEventListener('click', (e) => {
            if (e.target.classList.contains('filter-btn')) {
                this.filter = e.target.dataset.filter;
                this.render();
            }
            if (e.target.id === 'export-btn') {
                this.exportToExcel();
            }
        });
    }

    filterTrades(period) {
        const now = new Date(); // In real app, consider '2023-10-27' as today due to mock data
        // For Mock Data consistency, let's assume 'Today' is 2023-10-27
        const todayStr = '2023-10-27';
        const todayDate = new Date(todayStr);

        return this.trades.filter(trade => {
            const tDate = new Date(trade.time);
            const tDateStr = trade.time.split(' ')[0];

            switch(period) {
                case 'today':
                    return tDateStr === todayStr;
                case 'week':
                    const weekAgo = new Date(todayDate);
                    weekAgo.setDate(todayDate.getDate() - 7);
                    return tDate >= weekAgo;
                case 'month':
                    const monthAgo = new Date(todayDate);
                    monthAgo.setMonth(todayDate.getMonth() - 1);
                    return tDate >= monthAgo;
                default:
                    return true;
            }
        });
    }

    onCellEdit(cell, id, field) {
        console.log(`Updated Trade ${id} field ${field}:`, cell.innerText);
        // Sync with backend logic here
    }

    exportToExcel() {
        let table = document.getElementById("tradeBookTable");
        let rows = Array.from(table.rows);
        let csvContent = "data:text/csv;charset=utf-8,";

        rows.forEach(row => {
            let rowData = Array.from(row.cells).map(cell => {
                return cell.innerText.replace(/(\r\n|\n|\r)/gm, "").replace(/,/g, "");
            });
            csvContent += rowData.join(",") + "\r\n";
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `trade_book_${this.filter}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    initResizers() {
         document.querySelectorAll('.column-resizer').forEach(resizer => {
            resizer.addEventListener('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const th = resizer.parentElement;
                const startX = e.pageX;
                const startWidth = th.offsetWidth;

                function onMouseMove(e) {
                    const newWidth = startWidth + (e.pageX - startX);
                    th.style.width = newWidth + 'px';
                }

                function onMouseUp() {
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                }

                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
            });
            resizer.addEventListener('click', (e) => e.stopPropagation());
        });
    }

    sortTable(n) {
        // ... (Same sorting logic as before, or improved)
        const table = document.getElementById("tradeBookTable");
        let rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
        switching = true;
        dir = "asc";
        while (switching) {
            switching = false;
            rows = table.tBodies[0].rows;
            for (i = 0; i < (rows.length - 1); i++) {
                shouldSwitch = false;
                x = rows[i].getElementsByTagName("TD")[n];
                y = rows[i + 1].getElementsByTagName("TD")[n];
                let xVal = x.innerText.toLowerCase();
                let yVal = y.innerText.toLowerCase();
                if (!isNaN(parseFloat(xVal)) && !isNaN(parseFloat(yVal))) {
                        xVal = parseFloat(xVal);
                        yVal = parseFloat(yVal);
                }
                if (dir == "asc") {
                    if (xVal > yVal) { shouldSwitch = true; break; }
                } else if (dir == "desc") {
                    if (xVal < yVal) { shouldSwitch = true; break; }
                }
            }
            if (shouldSwitch) {
                rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                switching = true;
                switchcount ++;
            } else {
                if (switchcount == 0 && dir == "asc") {
                    dir = "desc";
                    switching = true;
                }
            }
        }
    }
}
