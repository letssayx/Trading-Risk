// Workbook Component
// Simple tabbed grid implementation

class Workbook {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        this.data = [
            { id: 1, time: '10:00', symbol: 'NIFTY', side: 'BUY', qty: 50, price: 21500, pnl: 1200 },
            { id: 2, time: '10:15', symbol: 'BANKNIFTY', side: 'SELL', qty: 25, price: 45000, pnl: -500 },
            { id: 3, time: '11:30', symbol: 'RELIANCE', side: 'BUY', qty: 100, price: 2400, pnl: 450 }
        ];
        this.render();
    }

    render() {
        // Find grid container
        const grid = document.getElementById('workbook-grid');
        if (!grid) return;

        let html = `
        <table class="trade-table" style="width:100%; border-collapse:collapse; font-size:0.85em;">
            <thead>
                <tr style="background:#252525;">
                    <th style="padding:6px; text-align:left;">ID</th>
                    <th style="padding:6px; text-align:left;">Time</th>
                    <th style="padding:6px; text-align:left;">Symbol</th>
                    <th style="padding:6px; text-align:left;">Side</th>
                    <th style="padding:6px; text-align:right;">Qty</th>
                    <th style="padding:6px; text-align:right;">Price</th>
                    <th style="padding:6px; text-align:right;">PnL</th>
                </tr>
            </thead>
            <tbody>`;

        this.data.forEach(row => {
            const pnlClass = row.pnl >= 0 ? 'color:#4caf50' : 'color:#f44336';
            const sideClass = row.side === 'BUY' ? 'color:#4caf50' : 'color:#f44336';

            html += `<tr style="border-bottom:1px solid #333;">
                <td style="padding:6px;">${row.id}</td>
                <td style="padding:6px;">${row.time}</td>
                <td style="padding:6px; font-weight:bold;">${row.symbol}</td>
                <td style="padding:6px; ${sideClass}">${row.side}</td>
                <td style="padding:6px; text-align:right;">${row.qty}</td>
                <td style="padding:6px; text-align:right;">${row.price}</td>
                <td style="padding:6px; text-align:right; ${pnlClass}">${row.pnl}</td>
            </tr>`;
        });

        html += `</tbody></table>`;
        grid.innerHTML = html;
    }
}

// Global function for toolbar button
window.wbShowOnChart = function() {
    alert("Showing workbook data on chart...");
    // Mock interaction
    if (window.chart) {
        // e.g. add markers
    }
};

document.addEventListener('DOMContentLoaded', () => {
    new Workbook('workbook-panel');

    // Tab switching logic (simple class toggle)
    document.querySelectorAll('.wb-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            if (tab.classList.contains('wb-tab-add')) return;
            document.querySelectorAll('.wb-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            // Logic to switch data source would go here
        });
    });
});
