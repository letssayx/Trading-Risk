const StatArbTab = {
    instances: [],
    container: null,

    init: function() {
        setInterval(() => this.pollAll(), 2000);
    },

    render: function(container) {
        this.container = container;
        container.innerHTML = `
            <div class="inner-tabs-bar" style="display:flex; gap:10px; align-items:center;">
                <input type="text" id="statarb-add-input" class="inline-input" placeholder="+ Pair (Format S1,S2,Ratio or S1,S2) Enter" style="width:250px;">
                <button id="statarb-remove-selected-btn" class="action-btn" style="color:#f44336; border: 1px solid #f44336; margin-left: auto; padding: 4px 8px;">Remove Selected</button>
            </div>
            <table class="strategy-table">
                <thead>
                    <tr>
                        <th style="width: 30px;"><input type="checkbox" id="statarb-select-all"></th>
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

        // Bind Remove Selected
        document.getElementById('statarb-remove-selected-btn').addEventListener('click', () => this.removeSelected());

        // Bind Select All
        document.getElementById('statarb-select-all').addEventListener('change', (e) => {
            const checked = e.target.checked;
            document.querySelectorAll('.statarb-row-checkbox').forEach(cb => cb.checked = checked);
        });

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

        const pauseText = inst.paused ? 'Resume' : 'Pause';
        const pauseColor = inst.paused ? '#4caf50' : '#ff9800'; // Green for Resume, Orange for Pause

        // Safety checks for values
        const spread = typeof s.spread === 'number' ? s.spread.toFixed(2) : '--';
        const z = typeof s.z_score === 'number' ? s.z_score.toFixed(2) : '--';
        const signal = s.signal || '--';

        inst.rowElement.innerHTML = `
            <td><input type="checkbox" class="statarb-row-checkbox" value="${inst.id}"></td>
            <td>${pairName}</td>
            <td>${spread}</td>
            <td>${z}</td>
            <td style="color:${this.getColor(signal)}">${signal}</td>
            <td>
                <div style="display:flex; gap:8px; align-items:center;">
                    <button class="action-btn" style="color:${pauseColor}; font-size:0.9em; border: 1px solid ${pauseColor}; padding: 2px 5px; border-radius: 4px;" title="${pauseText}" onclick="StatArbTab.togglePause('${inst.id}')">${pauseText}</button>
                </div>
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

    removeSelected: async function() {
        const checkboxes = document.querySelectorAll('.statarb-row-checkbox:checked');
        if(checkboxes.length === 0) return;

        if(!confirm(`Remove ${checkboxes.length} strategies?`)) return;

        const ids = Array.from(checkboxes).map(cb => cb.value);

        // Send all stop requests
        await Promise.all(ids.map(id => fetch(`/api/strategies/statarb/stop/${id}`, { method: 'POST' })));

        // Update local state locally
        this.instances = this.instances.filter(i => !ids.includes(i.id));
        this.renderRows();

        // Uncheck select all
        const selectAll = document.getElementById('statarb-select-all');
        if(selectAll) selectAll.checked = false;
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
