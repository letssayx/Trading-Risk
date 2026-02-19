const TurtleTab = {
    instances: [], // { id, symbol, segment, state, rowElement }
    container: null,

    init: function() {
        // Start polling loop
        setInterval(() => this.pollAll(), 2000);
    },

    render: function(container) {
        this.container = container;
        container.innerHTML = `
            <div class="inner-tabs-bar" style="display:flex; align-items:center; gap:10px;">
                <div style="position:relative;">
                    <input type="text" id="turtle-add-input" list="turtle-symbol-list" class="inline-input" placeholder="+ Symbol (Enter)" autocomplete="off">
                    <datalist id="turtle-symbol-list"></datalist>
                </div>

                <div class="segment-selector" style="font-size:0.85em; color:#ccc;">
                    <label style="margin-right:8px; cursor:pointer;">
                        <input type="radio" name="turtle-seg" value="CM" onclick="TurtleTab.toggleExpiry(false)"> EQ
                    </label>
                    <label style="cursor:pointer; margin-right:10px;">
                        <input type="radio" name="turtle-seg" value="FO" checked onclick="TurtleTab.toggleExpiry(true)"> Futures
                    </label>
                    <select id="turtle-expiry-pos" style="background:#222; color:#ccc; border:1px solid #444; border-radius:3px;">
                        <option value="1">Near (FUT1)</option>
                        <option value="2">Next (FUT2)</option>
                        <option value="3">Far (FUT3)</option>
                    </select>
                </div>
            </div>
            <table class="strategy-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Seg</th>
                        <th>Expiry</th>
                        <th>Price</th>
                        <th>N (ATR)</th>
                        <th>Signal</th>
                        <th>Stop</th>
                        <th>Pos Size</th>
                        <th>OI</th>
                        <th>Vol</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="turtle-table-body">
                </tbody>
            </table>
        `;

        // Bind Input
        const input = document.getElementById('turtle-add-input');

        // Autocomplete / Search
        input.addEventListener('input', this.debounce(async (e) => {
            const q = e.target.value;
            if (q.length < 2) return;

            const seg = document.querySelector('input[name="turtle-seg"]:checked').value;

            try {
                const res = await fetch(`/api/symbols/search?q=${q}&segment=${seg}`);
                const symbols = await res.json();
                const dl = document.getElementById('turtle-symbol-list');
                dl.innerHTML = symbols.map(s => `<option value="${s}">`).join('');
            } catch(e) { console.error(e); }
        }, 300));

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const val = e.target.value.trim().toUpperCase();
                if (val) {
                    this.startStrategy(val);
                    e.target.value = '';
                }
            }
        });

        this.renderRows();
    },

    startStrategy: async function(symbol) {
        // Get Segment & Expiry
        const seg = document.querySelector('input[name="turtle-seg"]:checked').value;
        const expiryPos = document.getElementById('turtle-expiry-pos').value;

        try {
            const res = await fetch('/api/strategies/turtle/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    symbol: symbol,
                    risk_per_trade: 0.01,
                    segment: seg,
                    expiry_pos: parseInt(expiryPos)
                })
            });
            const data = await res.json();

            this.instances.push({
                id: data.instanceId,
                symbol: symbol,
                segment: seg,
                expiry_pos: parseInt(expiryPos),
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
            alert("Failed to start strategy: " + e.message);
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

    toggleExpiry: function(show) {
        const el = document.getElementById('turtle-expiry-pos');
        if(el) el.style.display = show ? 'inline-block' : 'none';
    },

    updateRowDOM: function(inst) {
        if (!inst.rowElement) return;
        const s = inst.state;
        const isActive = s.active !== false; // Default true if undefined

        // Action Buttons
        const toggleBtn = isActive
            ? `<button onclick="TurtleTab.pause('${inst.id}')" style="color:orange;">Pause</button>`
            : `<button onclick="TurtleTab.resume('${inst.id}')" style="color:green;">Resume</button>`;

        const expiryLabel = inst.segment === 'FO' ? `FUT${inst.expiry_pos || 1}` : '--';
        const oi = s.oi ? s.oi.toLocaleString() : '--';
        const vol = s.volume ? s.volume.toLocaleString() : '--';

        inst.rowElement.innerHTML = `
            <td>${s.symbol || inst.symbol}</td>
            <td><span class="badge ${inst.segment}">${inst.segment}</span></td>
            <td>${expiryLabel}</td>
            <td>${s.price ? s.price.toFixed(2) : '--'}</td>
            <td>${s.n}</td>
            <td style="color:${this.getColor(s.signal)}">${s.signal}</td>
            <td>${s.stop}</td>
            <td>${s.position_size}</td>
            <td>${oi}</td>
            <td>${vol}</td>
            <td class="actions-cell">
                <button onclick="ChartTabs.addTab('${inst.symbol}', 'stock', '${inst.segment}', ${inst.expiry_pos || 1})" title="Show Chart">📈</button>
                ${toggleBtn}
                <button onclick="TurtleTab.remove('${inst.id}')" title="Remove">❌</button>
            </td>
        `;
    },

    getColor: function(sig) {
        if (sig === 'BUY') return '#4caf50';
        if (sig === 'SELL' || sig === 'STOP LOSS') return '#f44336';
        return '#ccc';
    },

    pause: async function(id) {
        await fetch(`/api/strategies/turtle/pause/${id}`, { method: 'POST' });
        // Optimistic update
        const inst = this.instances.find(i => i.id === id);
        if(inst) inst.state.active = false;
        this.updateRowDOM(inst);
    },

    resume: async function(id) {
        await fetch(`/api/strategies/turtle/resume/${id}`, { method: 'POST' });
        const inst = this.instances.find(i => i.id === id);
        if(inst) inst.state.active = true;
        this.updateRowDOM(inst);
    },

    remove: async function(id) {
        if(!confirm("Remove this strategy instance?")) return;
        await fetch(`/api/strategies/turtle/remove/${id}`, { method: 'POST' });
        this.instances = this.instances.filter(i => i.id !== id);
        this.renderRows();
    },

    pollAll: async function() {
        for (let i = this.instances.length - 1; i >= 0; i--) {
            const inst = this.instances[i];
            try {
                const res = await fetch(`/api/strategies/turtle/state/${inst.id}`);
                if(res.ok) {
                    const state = await res.json();
                    inst.state = state;
                    this.updateRowDOM(inst);
                } else if (res.status === 404) {
                    // Instance gone (server restart?), remove it
                    console.warn("Instance lost", inst.id);
                    if (inst.rowElement) inst.rowElement.remove();
                    this.instances.splice(i, 1);
                }
            } catch (e) { console.error(e); }
        }
    },

    handleTick: function(tick) {
        const inst = this.instances.find(i => i.symbol === tick.symbol);
        if (inst && inst.state.active !== false) {
            inst.state.price = tick.price;
            this.updateRowDOM(inst);
        }
    },

    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};
