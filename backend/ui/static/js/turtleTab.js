const TurtleTab = {
    instances: [], // { id, symbol, state, rowElement }
    container: null,

    init: function() {
        // Start polling loop
        setInterval(() => this.pollAll(), 2000);
    },

    render: function(container) {
        this.container = container;
        container.innerHTML = `
            <div class="inner-tabs-bar">
                <div class="inner-tab active" onclick="TurtleTab.openAddModal()">+ Add Symbol</div>
            </div>
            <table class="strategy-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Price</th>
                        <th>N (ATR)</th>
                        <th>Signal</th>
                        <th>Stop</th>
                        <th>Pos Size</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="turtle-table-body">
                </tbody>
            </table>
        `;
        this.renderRows();
    },

    openAddModal: function() {
        SymbolSearch.open((symbol) => {
            this.startStrategy(symbol);
        });
    },

    startStrategy: async function(symbol) {
        try {
            const res = await fetch('/api/strategies/turtle/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ symbol: symbol, risk_per_trade: 0.01 })
            });
            const data = await res.json();

            this.instances.push({
                id: data.instanceId,
                symbol: symbol,
                state: data.initialState,
                rowElement: null
            });

            this.renderRows();

            // Subscribe to live feed
            if (window.ws && window.ws.readyState === WebSocket.OPEN) {
                window.ws.send(JSON.stringify({ subscribe: [symbol] }));
            }

        } catch (e) {
            console.error("Failed to start Turtle", e);
        }
    },

    renderRows: function() {
        const tbody = document.getElementById('turtle-table-body');
        if (!tbody) return;
        tbody.innerHTML = '';

        this.instances.forEach(inst => {
            const tr = document.createElement('tr');
            inst.rowElement = tr;
            this.updateRowDOM(inst);
            tbody.appendChild(tr);
        });
    },

    updateRowDOM: function(inst) {
        if (!inst.rowElement) return;
        const s = inst.state;
        inst.rowElement.innerHTML = `
            <td>${inst.symbol}</td>
            <td>${s.price ? s.price.toFixed(2) : '--'}</td>
            <td>${s.n}</td>
            <td style="color:${this.getColor(s.signal)}">${s.signal}</td>
            <td>${s.stop}</td>
            <td>${s.position_size}</td>
            <td>
                <button onclick="ChartTabs.addTab('${inst.symbol}')">Show Chart</button>
                <button onclick="TurtleTab.stop('${inst.id}')">Stop</button>
            </td>
        `;
    },

    getColor: function(sig) {
        if (sig === 'BUY') return '#4caf50';
        if (sig === 'SELL' || sig === 'STOP LOSS') return '#f44336';
        return '#ccc';
    },

    stop: async function(id) {
        await fetch(`/api/strategies/turtle/stop/${id}`, { method: 'POST' });
        this.instances = this.instances.filter(i => i.id !== id);
        this.renderRows();
    },

    pollAll: async function() {
        for (let inst of this.instances) {
            try {
                const res = await fetch(`/api/strategies/turtle/state/${inst.id}`);
                const state = await res.json();
                inst.state = state;
                this.updateRowDOM(inst);
            } catch (e) { console.error(e); }
        }
    },

    handleTick: function(tick) {
        // Update price immediately if matching
        const inst = this.instances.find(i => i.symbol === tick.symbol);
        if (inst) {
            inst.state.price = tick.price;
            this.updateRowDOM(inst);
        }
    }
};
