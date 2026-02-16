class StatArbTab {
    constructor(container, tabData) {
        this.container = container;
        this.sym1 = tabData.sym1;
        this.sym2 = tabData.sym2;
        this.data = { p1: 0, p2: 0, spread: 0, z_score: 0, signal: 'WAIT' };
        this.render();
        this.startStream();
    }

    render() {
        const signalColor = this.data.signal === 'LONG' ? '#4caf50' : (this.data.signal === 'SHORT' ? '#f44336' : '#ccc');

        this.container.innerHTML = `
            <table class="trade-table">
                <thead>
                    <tr><th>Leg 1</th><th>Leg 2</th><th>Price 1</th><th>Price 2</th><th>Spread</th><th>Z-Score</th><th>Signal</th><th>Action</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="font-weight:bold;">${this.sym1}</td>
                        <td style="font-weight:bold;">${this.sym2}</td>
                        <td>${this.data.p1.toFixed(2)}</td>
                        <td>${this.data.p2.toFixed(2)}</td>
                        <td>${this.data.spread.toFixed(2)}</td>
                        <td>${this.data.z_score.toFixed(2)}</td>
                        <td style="color:${signalColor}; font-weight:bold;">${this.data.signal}</td>
                        <td><button class="wb-btn" onclick="window.wbManager.openChart('${this.sym1} vs ${this.sym2}')">📈 Chart</button></td>
                    </tr>
                </tbody>
            </table>
            <div style="padding:10px; font-size:0.8em; color:#666;">
                Status: Monitoring pair divergence...
            </div>
        `;
    }

    async update(p1, p2) {
        try {
            const response = await fetch('/api/strategies/statarb/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ sym1: this.sym1, sym2: this.sym2, price1: p1, price2: p2 })
            });
            const result = await response.json();
            this.data = result;
            this.render();
        } catch(e) {
            console.error("StatArb Update Failed", e);
        }
    }

    startStream() {
        // Mock Live Stream
        this.interval = setInterval(() => {
            const p1 = 100 + Math.random() * 2;
            const p2 = 100 + Math.random() * 2;
            this.update(p1, p2);
        }, 3000);
    }

    destroy() {
        clearInterval(this.interval);
    }
}

window.StatArbTab = StatArbTab;
