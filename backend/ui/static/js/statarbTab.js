const StatArbTab = {
    instances: [],
    container: null,

    init: function() {
        setInterval(() => this.pollAll(), 2000);
    },

    render: function(container) {
        this.container = container;
        container.innerHTML = `
            <div class="inner-tabs-bar">
                <div class="inner-tab active" onclick="StatArbTab.openAddModal()">+ Add Pair</div>
            </div>
            <table class="strategy-table">
                <thead>
                    <tr>
                        <th>Pair (S1-ratio*S2)</th>
                        <th>Spread</th>
                        <th>Z-Score</th>
                        <th>Signal</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="statarb-table-body">
                </tbody>
            </table>
        `;
        this.renderRows();
    },

    openAddModal: function() {
        // Needs 2 symbols. Simple prompt for MVP or create a custom modal.
        // Let's use prompts for simplicity as creating a multi-step modal is complex in one shot.
        const s1 = prompt("Enter Symbol 1 (Long Leg):", "NIFTY");
        if (!s1) return;
        const s2 = prompt("Enter Symbol 2 (Short Leg):", "BANKNIFTY");
        if (!s2) return;
        const ratio = prompt("Enter Ratio:", "1.0");

        this.startStrategy(s1, s2, parseFloat(ratio) || 1.0);
    },

    startStrategy: async function(s1, s2, ratio) {
        try {
            const res = await fetch('/api/strategies/statarb/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ symbol1: s1, symbol2: s2, ratio: ratio, z_threshold: 2.0 })
            });
            const data = await res.json();

            this.instances.push({
                id: data.instanceId,
                s1, s2, ratio,
                state: data.initialState,
                rowElement: null
            });

            this.renderRows();

        } catch (e) {
            console.error("Failed to start StatArb", e);
        }
    },

    renderRows: function() {
        const tbody = document.getElementById('statarb-table-body');
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
        const pairName = `${inst.s1} - ${inst.ratio}*${inst.s2}`;

        inst.rowElement.innerHTML = `
            <td>${pairName}</td>
            <td>${s.spread}</td>
            <td>${s.z_score}</td>
            <td style="color:${this.getColor(s.signal)}">${s.signal}</td>
            <td>
                <button onclick="ChartTabs.addTab('${pairName}', 'spread', {symbol1:'${inst.s1}', symbol2:'${inst.s2}', ratio:${inst.ratio}})">Show Chart</button>
                <button onclick="StatArbTab.stop('${inst.id}')">Stop</button>
            </td>
        `;
    },

    getColor: function(sig) {
        if (sig.includes('LONG')) return '#4caf50';
        if (sig.includes('SHORT')) return '#f44336';
        return '#ccc';
    },

    stop: async function(id) {
        await fetch(`/api/strategies/statarb/stop/${id}`, { method: 'POST' });
        this.instances = this.instances.filter(i => i.id !== id);
        this.renderRows();
    },

    pollAll: async function() {
        for (let inst of this.instances) {
            try {
                const res = await fetch(`/api/strategies/statarb/state/${inst.id}`);
                const state = await res.json();
                inst.state = state;
                this.updateRowDOM(inst);
            } catch (e) { console.error(e); }
        }
    },

    handleTick: function(tick) {
        // StatArb handle tick? Usually updates spread.
        // Since backend adapter simulates spread updates, we rely on poll.
        // Frontend calculation is possible but let's stick to polling for consistency with backend state.
    }
};
