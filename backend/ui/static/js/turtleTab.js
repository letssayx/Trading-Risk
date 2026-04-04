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
            <div class="inner-tabs-bar" style="display: flex; gap: 10px; align-items: center; justify-content: space-between;">
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="text" id="turtle-add-input" class="inline-input" placeholder="+ Symbol (Enter)" autocomplete="off" list="turtle-symbol-list">
                    <datalist id="turtle-symbol-list"></datalist>

                    <div style="display: flex; gap: 10px; font-size: 0.9em;">
                        <label><input type="radio" name="turtle-segment" value="EQ"> EQ</label>
                        <label><input type="radio" name="turtle-segment" value="FUT" checked> Futures</label>
                    </div>

                    <select id="turtle-expiry-select" style="background: #333; color: white; border: 1px solid #555; padding: 2px;">
                        <option value="NEAR">Near (FUT1)</option>
                        <option value="NEXT">Next (FUT2)</option>
                        <option value="FAR">Far (FUT3)</option>
                    </select>
                </div>
                <div>
                    <button onclick="TurtleTab.removeSelected()" class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.8em;">Remove Selected</button>
                </div>
            </div>
            <table class="strategy-table">
                <thead>
                    <tr>
                        <th style="width: 30px;"><input type="checkbox" id="turtle-check-all" onclick="TurtleTab.toggleAll(this)"></th>
                        <th>Symbol</th>
                        <th>Price</th>
                        <th>N (ATR)</th>
                        <th>Signal</th>
                        <th>Stop</th>
                        <th>Pos Size</th>
                        <th>Expiry</th>
                        <th>OI</th>
                        <th>Volume</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="turtle-table-body">
                </tbody>
            </table>
        `;

        // Bind Input
        const input = document.getElementById('turtle-add-input');
        const segmentRadios = document.querySelectorAll('input[name="turtle-segment"]');
        const expirySelect = document.getElementById('turtle-expiry-select');
        const datalist = document.getElementById('turtle-symbol-list');

        // Segment Change Handler
        segmentRadios.forEach(r => r.addEventListener('change', (e) => {
            if (e.target.value === 'EQ') {
                expirySelect.style.display = 'none';
            } else {
                expirySelect.style.display = 'block';
            }
            input.value = ''; // Clear input on switch
        }));

        // Search/Autocomplete Handler
        input.addEventListener('input', async (e) => {
            const query = e.target.value.trim();
            if (query.length < 2) return;

            const segment = document.querySelector('input[name="turtle-segment"]:checked').value;
            const apiSegment = segment === 'FUT' ? 'FO' : 'EQ';

            try {
                const res = await fetch(`/api/symbols/search?q=${query}&segment=${apiSegment}`);
                const results = await res.json();

                datalist.innerHTML = '';
                results.forEach(sym => {
                    const opt = document.createElement('option');
                    opt.value = sym;
                    datalist.appendChild(opt);
                });
            } catch (err) {
                console.error("Search failed", err);
            }
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                let val = e.target.value.trim().toUpperCase();
                if (!val) return;

                const segment = document.querySelector('input[name="turtle-segment"]:checked').value;
                if (segment === 'FUT') {
                    const expiry = document.getElementById('turtle-expiry-select').value;
                    if (!val.endsWith('FUT') && !val.endsWith('CE') && !val.endsWith('PE')) {
                        this.resolveContract(val, expiry).then(contract => {
                            if(contract) this.startStrategy(contract);
                            else alert("Could not resolve futures contract for " + val);
                        });
                        e.target.value = '';
                        return;
                    }
                }

                this.startStrategy(val);
                e.target.value = '';
            }
        });
    },

    resolveContract: async function(underlying, expiryType) {
        try {
            const res = await fetch(`/api/symbols/search?q=${underlying}&segment=FO`);
            const contracts = await res.json();
            if (contracts.length > 0) {
                if (expiryType === 'NEAR') return contracts[0];
                if (expiryType === 'NEXT') return contracts[1] || contracts[0];
                if (expiryType === 'FAR') return contracts[2] || contracts[contracts.length-1];
            }
            return null;
        } catch (e) {
            console.error(e);
            return null;
        }
    },

    startStrategy: async function(symbol) {
        try {
            const res = await fetch('/api/strategies/turtle/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ symbol: symbol, risk_per_trade: 0.01 })
            });

            if (!res.ok) throw new Error("Failed to start strategy");

            const data = await res.json();

            this.instances.push({
                id: data.instanceId,
                symbol: symbol,
                state: data.initialState,
                rowElement: null,
                selected: false
            });

            this.renderRows();

            if (window.ws && window.ws.readyState === WebSocket.OPEN) {
                window.ws.send(JSON.stringify({ subscribe: [symbol] }));
            }

        } catch (e) {
            console.error("Failed to start Turtle", e);
            alert(e.message); // Should handle gracefully
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
        const activeText = s.active ? "Pause" : "Start";

        inst.rowElement.innerHTML = `
            <td><input type="checkbox" onchange="TurtleTab.toggleSelect('${inst.id}', this.checked)" ${inst.selected ? 'checked' : ''}></td>
            <td>${inst.symbol}</td>
            <td>${s.price ? s.price.toFixed(2) : '--'}</td>
            <td>${s.n}</td>
            <td style="color:${this.getColor(s.signal)}">${s.signal}</td>
            <td>${s.stop}</td>
            <td>${s.position_size}</td>
            <td>${s.expiry || '--'}</td>
            <td>${s.oi || '--'}</td>
            <td>${s.volume || '--'}</td>
            <td>
                <button onclick="ChartTabs.addTab('${inst.symbol}')" title="Chart">📈</button>
                <button onclick="TurtleTab.togglePause('${inst.id}')" style="min-width: 50px;">${activeText}</button>
            </td>
        `;
    },

    getColor: function(sig) {
        if (sig === 'BUY') return '#3176B8';
        if (sig === 'SELL' || sig === 'STOP LOSS') return '#f44336';
        return '#ccc';
    },

    toggleSelect: function(id, checked) {
        const inst = this.instances.find(i => i.id === id);
        if(inst) inst.selected = checked;
    },

    toggleAll: function(checkbox) {
        const checked = checkbox.checked;
        this.instances.forEach(i => i.selected = checked);
        this.renderRows();
    },

    removeSelected: async function() {
        const toRemove = this.instances.filter(i => i.selected);
        for(let inst of toRemove) {
            await this.stop(inst.id);
        }
    },

    stop: async function(id) {
        await fetch(`/api/strategies/turtle/stop/${id}`, { method: 'POST' });
        this.instances = this.instances.filter(i => i.id !== id);
        this.renderRows();
    },

    togglePause: async function(id) {
        // Mock toggle locally
        const inst = this.instances.find(i => i.id === id);
        if(inst) {
            inst.state.active = !inst.state.active;
            this.updateRowDOM(inst);
        }
    },

    pollAll: async function() {
        for (let inst of this.instances) {
            try {
                const res = await fetch(`/api/strategies/turtle/state/${inst.id}`);
                const state = await res.json();
                inst.state = { ...inst.state, ...state };
                this.updateRowDOM(inst);
            } catch (e) { console.error(e); }
        }
    },

    handleTick: function(tick) {
        const inst = this.instances.find(i => i.symbol === tick.symbol);
        if (inst) {
            inst.state.price = tick.price;
            this.updateRowDOM(inst);
        }
    }
};
