const RolloverTab = {
    container: null,

    init: function() {},

    render: function(container) {
        this.container = container;
        container.innerHTML = `
            <div style="padding: 10px;">
                <div style="display:flex; gap:10px; margin-bottom:10px;">
                    <input type="text" id="rollover-symbol" placeholder="Symbol (e.g. NIFTY)" style="padding: 6px; background: #222; border: 1px solid #444; color: #fff;">
                    <button class="btn btn-secondary" onclick="RolloverTab.analyze()">Analyze</button>
                </div>

                <table class="strategy-table">
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th colspan="3" style="text-align:center; border-bottom:1px solid #444;">Near - Next</th>
                            <th colspan="3" style="text-align:center; border-bottom:1px solid #444;">Next - Far</th>
                        </tr>
                        <tr>
                            <th></th>
                            <th>Basis</th>
                            <th>Ann %</th>
                            <th>Z-Score</th>
                            <th>Basis</th>
                            <th>Ann %</th>
                            <th>Z-Score</th>
                        </tr>
                    </thead>
                    <tbody id="rollover-results">
                        <tr><td colspan="7" style="text-align:center; color:#666;">Enter symbol to analyze</td></tr>
                    </tbody>
                </table>
            </div>
        `;
    },

    analyze: async function() {
        const symbol = document.getElementById('rollover-symbol').value.toUpperCase();
        const tbody = document.getElementById('rollover-results');

        if (!symbol) return;

        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Analyzing...</td></tr>';

        try {
            const res = await fetch('/api/strategies/rollover/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ symbol: symbol, lookback: 24 })
            });
            const data = await res.json();

            if (res.ok) {
                const nn = data.near_next || {};
                const nf = data.next_far || {};

                tbody.innerHTML = `
                    <tr>
                        <td>${symbol}</td>
                        <td style="color:${nn.basis > 0 ? '#4caf50' : '#f44336'}">${nn.basis ? nn.basis.toFixed(2) : '--'}</td>
                        <td>${nn.annualized_pct ? nn.annualized_pct.toFixed(2) + '%' : '--'}</td>
                        <td style="font-weight:bold; color:${this.getZColor(nn.z_score)}">${nn.z_score ? nn.z_score.toFixed(2) : '--'}</td>

                        <td style="color:${nf.basis > 0 ? '#4caf50' : '#f44336'}">${nf.basis ? nf.basis.toFixed(2) : '--'}</td>
                        <td>${nf.annualized_pct ? nf.annualized_pct.toFixed(2) + '%' : '--'}</td>
                        <td style="font-weight:bold; color:${this.getZColor(nf.z_score)}">${nf.z_score ? nf.z_score.toFixed(2) : '--'}</td>
                    </tr>
                `;
            } else {
                tbody.innerHTML = `<tr><td colspan="7" style="color:red;">Error: ${data.detail}</td></tr>`;
            }

        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="7" style="color:red;">Error: ${e.message}</td></tr>`;
        }
    },

    getZColor: function(z) {
        if (!z) return '#ccc';
        if (z > 1.5) return '#f44336'; // Expensive
        if (z < -1.5) return '#4caf50'; // Cheap
        return '#ccc';
    },

    handleTick: function(tick) {}
};
