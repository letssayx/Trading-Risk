const PriceOiTool = {
    active: false,
    containerId: 'price-oi-container',

    init: function() {
        // Create container if not exists, but usually we render into an existing area
    },

    open: function() {
        this.active = true;

        // 1. Create a new tab in the strategy workbench if not exists
        let tab = document.querySelector('.wb-tab[data-type="price-oi"]');
        if (!tab) {
            const header = document.querySelector('.wb-tabs-header');
            tab = document.createElement('div');
            tab.className = 'wb-tab';
            tab.dataset.type = 'price-oi';
            tab.innerText = 'Price-OI Analysis';
            tab.onclick = () => WorkbookManager.switchTab('price-oi');

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

        // 2. Switch to it
        WorkbookManager.switchTab('price-oi');
    },

    close: function() {
        this.active = false;
        const tab = document.querySelector('.wb-tab[data-type="price-oi"]');
        if (tab) tab.remove();

        // Switch back to default
        WorkbookManager.switchTab('turtle');
    },

    render: function(container) {
        container.innerHTML = `
            <div style="padding: 10px; color: #ccc;">
                <h3>Price vs OI Analysis</h3>
                <div style="margin-bottom: 10px; display: flex; gap: 10px;">
                    <input type="text" id="poi-symbol" placeholder="Symbol (e.g. NIFTY)" style="padding: 5px; background: #333; color: white; border: 1px solid #555;">
                    <button onclick="PriceOiTool.analyze()" class="btn btn-primary">Analyze</button>
                </div>
                <div id="poi-results">
                    <p>Select a symbol to view Price vs OI trends.</p>
                </div>
            </div>
        `;

        // Add enter key support
        document.getElementById('poi-symbol').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') PriceOiTool.analyze();
        });
    },

    analyze: async function() {
        const symbol = document.getElementById('poi-symbol').value.toUpperCase();
        const resultsDiv = document.getElementById('poi-results');

        if (!symbol) return;

        resultsDiv.innerHTML = 'Loading...';

        // Mock Data for now as backend might not have the full Price-OI endpoint yet
        // In a real scenario, we would fetch from /api/analysis/price-oi

        // Search for futures to verify symbol exists or get contract
        try {
            const searchRes = await fetch(`/api/symbols/search?q=${symbol}&segment=FO`);
            const contracts = await searchRes.json();

            let html = `<p>Found ${contracts.length} contracts for ${symbol}:</p>`;
            html += `<ul style="max-height: 100px; overflow-y: auto;">`;
            contracts.forEach(c => html += `<li>${c}</li>`);
            html += `</ul>`;

            html += `<div style="margin-top: 20px; border: 1px solid #444; padding: 20px; text-align: center;">
                [Chart Placeholder: Price vs OI for ${symbol}]<br>
                <em>Long Build Up / Short Covering analysis would appear here.</em>
            </div>`;

            resultsDiv.innerHTML = html;

        } catch (e) {
            resultsDiv.innerHTML = `<p style="color: red;">Error: ${e.message}</p>`;
        }
    },

    handleTick: function(tick) {
        // Update if active
    }
};

// Register with WorkbookManager if possible, or just let WorkbookManager handle unknown types?
// We need to inject this into WorkbookManager.modules
window.addEventListener('load', () => {
   if (window.WorkbookManager) {
       window.WorkbookManager.modules['price-oi'] = PriceOiTool;
   }
});
