const RolloverTool = {
    active: false,
    containerId: 'rollover-container',

    init: function() {
        // Create container if not exists
    },

    open: function() {
        this.active = true;

        let tab = document.querySelector('.wb-tab[data-type="rollover"]');
        if (!tab) {
            const header = document.querySelector('.wb-tabs-header');
            tab = document.createElement('div');
            tab.className = 'wb-tab';
            tab.dataset.type = 'rollover';
            tab.innerText = 'Rollover Analysis';
            tab.onclick = () => WorkbookManager.switchTab('rollover');

            // Add close button
            const closeBtn = document.createElement('span');
            closeBtn.innerText = ' ×';
            closeBtn.style.cursor = 'pointer';
            closeBtn.style.marginLeft = '5px';
            closeBtn.onclick = (e) => {
                e.stopPropagation();
                this.close();
            };
            tab.appendChild(closeBtn);

            header.appendChild(tab);
        }

        WorkbookManager.switchTab('rollover');
    },

    close: function() {
        this.active = false;
        const tab = document.querySelector('.wb-tab[data-type="rollover"]');
        if (tab) tab.remove();
        WorkbookManager.switchTab('turtle');
    },

    render: function(container) {
        container.innerHTML = `
            <div style="padding: 10px; color: #ccc;">
                <h3>Rollover Analysis</h3>
                <div style="margin-bottom: 10px; display: flex; gap: 10px;">
                    <input type="text" id="rollover-symbol" placeholder="Symbol (e.g. NIFTY)" style="padding: 5px; background: #333; color: white; border: 1px solid #555;">
                    <button onclick="RolloverTool.analyze()" class="btn btn-primary">Analyze</button>
                </div>
                <div id="rollover-results">
                    <p>Select a symbol to view Rollover % and cost.</p>
                </div>
            </div>
        `;

        document.getElementById('rollover-symbol').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') RolloverTool.analyze();
        });
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
