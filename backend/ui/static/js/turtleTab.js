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

            // If Futures, we want to auto-suggest the Near Month Contract
            // But search API returns list of futures if we ask for FO.

            try {
                const res = await fetch(`/api/symbols/search?q=${query}&segment=${apiSegment}`);
                const results = await res.json();

                datalist.innerHTML = '';
                results.forEach(sym => {
                    const opt = document.createElement('option');
                    opt.value = sym;
                    datalist.appendChild(opt);
                });

                // If the user typed an exact underlying (e.g. BDL) and we are in FUT mode,
                // and the results contain BDL26FEBFUT (or similar), we want to help them select it.
                if (segment === 'FUT' && results.length > 0) {
                     // Find the first result that starts with the query and has FUT suffix
                     // ContractManager returns standardized suffix like 26FEBFUT
                     const nearMatch = results.find(s => s.startsWith(query.toUpperCase()));
                     // We don't force replace value yet, just show options.
                     // But if they hit enter on "BDL", we resolve it in keydown handler.
                }
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
                    // If user typed underlying (e.g. NIFTY) but not full contract, try to synthesize
                    // However, our search autocomplete should have provided the full contract.
                    // If the user just pressed enter on "NIFTY", we default to Near Month based on dropdown?
                    const expiry = document.getElementById('turtle-expiry-select').value; // NEAR, NEXT, FAR

                    // Basic heuristic: if it doesn't end in FUT/CE/PE, assume it's underlying and we need to find contract
                    if (!val.endsWith('FUT') && !val.endsWith('CE') && !val.endsWith('PE')) {
                        // We need to ask backend for the specific contract
                        // For now, let's assume the user picks from the list.
                        // But if they didn't, we can try to fetch the list and pick the one matching expiry
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
            // contracts is likely [NEAR, NEXT, FAR] sorted
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
