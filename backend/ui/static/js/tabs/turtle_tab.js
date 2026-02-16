class TurtleTab {
    constructor(container, tabData) {
        this.container = container;
        this.symbol = tabData.symbol;
        this.data = { price: 0, n: 0, signal: 'WAIT', stop: 0, size: 0 };
        this.render();
        this.startStream();
    }

    render() {
        const signalColor = this.data.signal === 'BUY' ? '#4caf50' : (this.data.signal === 'SELL' ? '#f44336' : '#ccc');

        this.container.innerHTML = `
            <table class="trade-table">
                <thead>
                    <tr><th>Symbol</th><th>Last Price</th><th>N (Vol)</th><th>Signal</th><th>Stop Level</th><th>Unit Size</th><th>Action</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="font-weight:bold;">${this.symbol}</td>
                        <td>${this.data.price.toFixed(2)}</td>
                        <td>${this.data.n.toFixed(2)}</td>
                        <td style="color:${signalColor}; font-weight:bold;">${this.data.signal}</td>
                        <td>${this.data.stop.toFixed(2)}</td>
                        <td>${this.data.size}</td>
                        <td><button class="wb-btn" onclick="window.wbManager.openChart('${this.symbol}')">📈 Chart</button></td>
                    </tr>
                </tbody>
            </table>
            <div style="padding:10px; font-size:0.8em; color:#666;">
                Status: Monitoring live ticks...
            </div>
        `;
    }

    async update(price) {
        // 1. Fetch Strategy State from Backend
        try {
            const response = await fetch('/api/strategies/turtle/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ symbol: this.symbol, price: price })
            });
            const result = await response.json();
            this.data = result;
            this.render();
        } catch(e) {
            console.error("Turtle Update Failed", e);
        }
    }

    startStream() {
        // Mock Live Stream for MVP
        this.interval = setInterval(() => {
            const mockPrice = 100 + Math.random() * 5;
            this.update(mockPrice);
        }, 3000); // Update every 3s
    }

    destroy() {
        clearInterval(this.interval);
    }
}

window.TurtleTab = TurtleTab;
