const RolloverTool = {
    active: false,
    containerId: 'deriv-tab-rollover',

    init: function() {
        const container = document.getElementById(this.containerId);
        if (container && !container.innerHTML.includes('rollover-symbol')) {
            this.render(container);
        }
    },

    open: function() {
        this.active = true;
        this.init();
    },

    close: function() {
        this.active = false;
    },

    render: function(container) {
        container.innerHTML = `
            <div style="color: #ccc; height: 100%; display: flex; flex-direction: column;">
                <div style="display: flex; gap: 15px; margin-bottom: 15px; align-items: center; flex-shrink: 0;">
                    <h2 style="margin: 0; color: #fff; font-size: 18px;">Rollover Analysis</h2>
                    <input type="text" id="rollover-symbol" class="form-control history-input" placeholder="Symbol (e.g. NIFTY)" style="width: 150px; padding: 4px;">
                    <button onclick="RolloverTool.analyze()" class="btn btn-primary">Analyze</button>
                </div>
                <div id="rollover-results" style="flex: 1; overflow: auto;">
                    <p style="text-align: center; color: #888; margin-top: 20px;">Select a symbol to view Rollover % and cost.</p>
                </div>
            </div>
        `;

        const input = document.getElementById('rollover-symbol');
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') RolloverTool.analyze();
            });
            if (typeof setupAutocomplete === 'function') {
                setupAutocomplete('rollover-symbol');
            }
        }
    },

    analyze: async function() {
        const symbol = document.getElementById('rollover-symbol').value.toUpperCase();
        const resultsDiv = document.getElementById('rollover-results');

        if (!symbol) return;

        resultsDiv.innerHTML = 'Loading Rollover Data...';

        try {
            const res = await fetch(`/api/analysis/rollover/${symbol}`);
            if (!res.ok) throw new Error("Analysis failed");
            const data = await res.json();

            let html = `<div style="padding: 20px; border: 1px solid #444; background: #222;">
                <h4>${symbol} Rollover Stats</h4>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 10px;">
                    <div>
                        <div style="font-size: 0.9em; color: #888;">Rollover %</div>
                        <div style="font-size: 1.5em; color: #00bcd4;">${data.rollover_pct}%</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; color: #888;">Rollover Cost (Spread)</div>
                        <div style="font-size: 1.5em; color: #4caf50;">${data.rollover_cost} (${data.rollover_cost_pct}%)</div>
                    </div>
                </div>

                <table style="width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 0.9em;">
                    <thead>
                        <tr style="background: #333;">
                            <th style="padding: 5px;">Contract</th>
                            <th style="padding: 5px;">Expiry</th>
                            <th style="padding: 5px;">Price</th>
                            <th style="padding: 5px;">OI</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 5px; border: 1px solid #444;">Near Month</td>
                            <td style="padding: 5px; border: 1px solid #444;">${data.near_month.expiry}</td>
                            <td style="padding: 5px; border: 1px solid #444;">${data.near_month.price}</td>
                            <td style="padding: 5px; border: 1px solid #444;">${data.near_month.oi}</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px; border: 1px solid #444;">Next Month</td>
                            <td style="padding: 5px; border: 1px solid #444;">${data.next_month.expiry}</td>
                            <td style="padding: 5px; border: 1px solid #444;">${data.next_month.price}</td>
                            <td style="padding: 5px; border: 1px solid #444;">${data.next_month.oi}</td>
                        </tr>
                    </tbody>
                </table>
            </div>`;

            resultsDiv.innerHTML = html;

        } catch (e) {
            resultsDiv.innerHTML = `<p style="color: red;">Error: ${e.message}</p>`;
        }
    },

    handleTick: function(tick) {
        // Update
    }
};

// Register
window.addEventListener('load', () => {
   if (window.WorkbookManager) {
       window.WorkbookManager.modules['rollover'] = RolloverTool;
   }
});
