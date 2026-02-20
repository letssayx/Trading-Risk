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
                <input type="text" id="statarb-add-input" class="inline-input" placeholder="+ Pair (Format S1,S2,Ratio or S1,S2) Enter" style="width:250px;">
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

        // Bind Input
        const input = document.getElementById('statarb-add-input');
        if(input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const val = e.target.value.trim().toUpperCase();
                    if (val) {
                        // Simple parser: S1,S2,Ratio
                        const parts = val.split(',');
                        if (parts.length >= 2) {
                            const s1 = parts[0].trim();
                            const s2 = parts[1].trim();
                            const ratio = parts.length > 2 ? parseFloat(parts[2]) : 1.0;
                            this.startStrategy(s1, s2, ratio);
                            e.target.value = '';
                        } else {
                            alert("Format: Symbol1, Symbol2, Ratio (optional)");
                        }
                    }
                }
            });
        }

        this.renderRows();
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
                state: data.initialState || { spread:0, z_score:0, signal:'NEUTRAL' },
                paused: false,
                rowElement: null
            });

            this.renderRows();

        } catch (e) {
            console.error("Failed to start StatArb", e);
            alert("Error starting strategy");
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
        const s = inst.state || {};
        const pairName = `${inst.s1} - ${inst.ratio}*${inst.s2}`;
        const pauseColor = inst.paused ? '#ff9800' : '#ccc';

        // Safety checks for values
        const spread = typeof s.spread === 'number' ? s.spread.toFixed(2) : '--';
        const z = typeof s.z_score === 'number' ? s.z_score.toFixed(2) : '--';
        const signal = s.signal || '--';

        inst.rowElement.innerHTML = `
            <td>${pairName}</td>
            <td>${spread}</td>
            <td>${z}</td>
            <td style="color:${this.getColor(signal)}">${signal}</td>
            <td style="display:flex; gap:5px; border:none;">
                <button class="action-btn" title="Add to Chart" onclick="ChartTabs.addTab('${pairName}', 'spread', {symbol1:'${inst.s1}', symbol2:'${inst.s2}', ratio:${inst.ratio}})">📈</button>
                <button class="action-btn" title="Pause" style="color:${pauseColor}" onclick="StatArbTab.togglePause('${inst.id}')">⏸️</button>
                <button class="action-btn" title="Remove" style="color:#f44336" onclick="StatArbTab.stop('${inst.id}')">❌</button>
            </td>
        `;
    },

    getColor: function(sig) {
        if (!sig) return '#ccc';
        if (sig.includes('LONG')) return '#4caf50';
        if (sig.includes('SHORT')) return '#f44336';
        return '#ccc';
    },

    togglePause: function(id) {
        const inst = this.instances.find(i => i.id === id);
        if(inst) {
            inst.paused = !inst.paused;
            // Notify backend if needed, but for now purely frontend state for polling control
            console.log(`Instance ${id} paused: ${inst.paused}`);
            this.updateRowDOM(inst);
        }
    },

    stop: async function(id) {
        try {
            await fetch(`/api/strategies/statarb/stop/${id}`, { method: 'POST' });
        } catch(e) { console.error(e); }

        this.instances = this.instances.filter(i => i.id !== id);
        this.renderRows();
    },

    pollAll: async function() {
        for (let inst of this.instances) {
            if(inst.paused) continue;
            try {
                const res = await fetch(`/api/strategies/statarb/state/${inst.id}`);
                if(res.ok) {
                    const state = await res.json();
                    inst.state = state;
                    this.updateRowDOM(inst);
                }
            } catch (e) { console.error(e); }
        }
    },

    handleTick: function(tick) {
        // Optional real-time update logic
    }
};
