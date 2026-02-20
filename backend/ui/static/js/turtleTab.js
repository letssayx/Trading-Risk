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
            <div class="inner-tabs-bar" style="display: flex; gap: 10px; align-items: center;">
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
            <table class="strategy-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Price</th>
                        <th>N (ATR)</th>
                        <th>Signal</th>
                        <th>Stop</th>
                        <th>Pos Size</th>
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
                    // For Futures, 'sym' is already the full contract (e.g., RELIANCE24FEBFUT)
                    // The backend `search_symbols` for 'FO' returns synthesized contracts.
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

                // If user selected from datalist or typed full contract, 'val' is correct.
                // If user typed 'RELIANCE' and hit enter while on FUT mode:
                if (segment === 'FUT') {
                    const expiry = document.getElementById('turtle-expiry-select').value; // NEAR, NEXT, FAR

                    // Basic heuristic: if it doesn't end in FUT/CE/PE, assume it's underlying and we need to find contract
                    if (!val.endsWith('FUT') && !val.endsWith('CE') && !val.endsWith('PE')) {
                        // User typed underlying (e.g. BDL), resolve to contract
                        this.resolveContract(val, expiry).then(contract => {
                            if(contract) {
                                // Update input to show resolved contract
                                input.value = contract;
                                this.startStrategy(contract);
                            }
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
            // Search for FO contracts for this underlying
            const res = await fetch(`/api/symbols/search?q=${underlying}&segment=FO`);
            const contracts = await res.json();

            // contracts should be list of full symbols like ['BDL24FEBFUT', 'BDL24MARFUT', ...]
            // Assuming sorted by date (MarketDataService sorts by expiry)

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
            const data = await res.json();

            this.instances.push({
                id: data.instanceId,
                symbol: symbol,
                state: data.initialState,
                paused: false,
                rowElement: null
            });

            this.renderRows();

        } catch (e) {
            console.error("Failed to start Turtle", e);
            alert("Failed to start strategy. Check console.");
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
        const pauseColor = inst.paused ? '#ff9800' : '#ccc';

        inst.rowElement.innerHTML = `
            <td>${inst.symbol}</td>
            <td>${s.price ? s.price.toFixed(2) : '--'}</td>
            <td>${s.n}</td>
            <td style="color:${this.getColor(s.signal)}">${s.signal}</td>
            <td>${s.stop}</td>
            <td>${s.position_size}</td>
            <td>${s.oi || '--'}</td>
            <td>${s.volume || '--'}</td>
            <td>
                <div style="display:flex; gap:5px;">
                    <button class="action-btn" title="Add to Chart" onclick="ChartTabs.addTab('${inst.symbol}', 'stock')">Chart</button>
                    <button class="action-btn" title="Pause" style="color:${pauseColor}" onclick="TurtleTab.togglePause('${inst.id}')">Pause</button>
                    <button class="action-btn" title="Remove" style="color:#f44336" onclick="TurtleTab.stop('${inst.id}')">Remove</button>
                </div>
            </td>
        `;
    },

    getColor: function(sig) {
        if (sig === 'BUY') return '#4caf50';
        if (sig === 'SELL' || sig === 'STOP LOSS') return '#f44336';
        return '#ccc';
    },

    togglePause: function(id) {
        const inst = this.instances.find(i => i.id === id);
        if(inst) {
            inst.paused = !inst.paused;
            console.log(`Turtle instance ${id} paused: ${inst.paused}`);
            this.updateRowDOM(inst);
        }
    },

    stop: async function(id) {
        await fetch(`/api/strategies/turtle/stop/${id}`, { method: 'POST' });
        this.instances = this.instances.filter(i => i.id !== id);
        this.renderRows();
    },

    pollAll: async function() {
        for (let inst of this.instances) {
            if (inst.paused) continue;
            try {
                const res = await fetch(`/api/strategies/turtle/state/${inst.id}`);
                const state = await res.json();
                inst.state = state;
                this.updateRowDOM(inst);
            } catch (e) { console.error(e); }
        }
    }
};
