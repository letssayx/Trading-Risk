class TradeBook {
    constructor(containerId) {
        this.containerId = containerId;
        this.trades = [];
        this.filter = 'today';

        // Mock Data
        this.trades = [
            { id: '#1024', time: '10:45', symbol: 'NIFTY 24000 CE', side: 'BUY', qty: 500, pnl: 3250.00, strategy: 'Turtle' },
            { id: '#1023', time: '10:42', symbol: 'BANKNIFTY', side: 'SELL', qty: 30, pnl: 600.00, strategy: 'StatArb' }
        ];

        this.init();
    }

    init() {
        this.render();
    }

    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // If table exists, update body, else create
        let tbody = container.querySelector('tbody');
        if (!tbody) {
            // If container is just a div, we might need to find the table or inject one if empty
            // The new layout has a static table with ID #tradeBookTable inside the container
            const table = document.getElementById('tradeBookTable');
            if (table) tbody = table.querySelector('tbody');
        }

        if (tbody) {
            tbody.innerHTML = this.trades.map(t => `
                <tr>
                    <td>${t.id}</td>
                    <td>${t.time}</td>
                    <td>${t.symbol}</td>
                    <td style="color:${t.side==='BUY'?'#4CAF50':'#F44336'}">${t.side}</td>
                    <td>${t.qty}</td>
                    <td class="${t.pnl>=0?'positive':'negative'}">${t.pnl > 0 ? '+' : ''}${t.pnl}</td>
                    <td>${t.strategy}</td>
                </tr>
            `).join('');
        }
    }
}

// Auto-init if container exists
if(document.getElementById('tradeBookContainer') || document.getElementById('tradeBookTable')) {
    // Determine container. The new layout has #tradeBookContainer wrapping the table
    // But the table itself has the ID #tradeBookTable.
    // We can attach to the wrapper or just manipulate the table.
    window.tradeBook = new TradeBook('tradeBookContainer');
}
