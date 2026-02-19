const OiTool = {
    active: false,
    containerId: 'oi-container',

    init: function() {
        // Create container if not exists, but usually we render into an existing area
    },

    open: function() {
        this.active = true;

        // 1. Create a new tab in the strategy workbench if not exists
        let tab = document.querySelector('.wb-tab[data-type="oi"]');
        if (!tab) {
            const header = document.querySelector('.wb-tabs-header');
            tab = document.createElement('div');
            tab.className = 'wb-tab';
            tab.dataset.type = 'oi';
            tab.innerText = 'OI Analysis';
            tab.onclick = () => WorkbookManager.switchTab('oi');

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
        WorkbookManager.switchTab('oi');
    },

    close: function() {
        this.active = false;
        const tab = document.querySelector('.wb-tab[data-type="oi"]');
        if (tab) tab.remove();

        // Switch back to default
        WorkbookManager.switchTab('turtle');
    },

    render: function(container) {
        container.innerHTML = `
            <div style="padding: 10px; color: #ccc; height: 100%; display: flex; flex-direction: column;">
                <h3>OI Analysis (Quadrant Visualizer)</h3>
                <div style="margin-bottom: 10px; display: flex; gap: 10px;">
                    <input type="text" id="oi-symbol" placeholder="Symbol (e.g. NIFTY)" style="padding: 5px; background: #333; color: white; border: 1px solid #555;">
                    <button onclick="OiTool.analyze()" class="btn btn-primary">Analyze</button>
                </div>
                <div id="oi-chart-area" style="flex: 1; background: #1a1a1a; position: relative;">
                    <p style="padding: 20px;">Select a symbol to visualize Price vs OI quadrants.</p>
                </div>
            </div>
        `;

        // Add enter key support
        document.getElementById('oi-symbol').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') OiTool.analyze();
        });
    },

    analyze: async function() {
        const symbol = document.getElementById('oi-symbol').value.toUpperCase();
        const chartArea = document.getElementById('oi-chart-area');

        if (!symbol) return;

        chartArea.innerHTML = 'Loading Analysis...';

        try {
            const res = await fetch(`/api/analysis/oi/${symbol}`);
            if (!res.ok) throw new Error("Analysis failed");
            const data = await res.json();

            // Render Plotly Chart
            this.renderChart(chartArea, data);

        } catch (e) {
            chartArea.innerHTML = `<p style="color: red; padding: 20px;">Error: ${e.message}</p>`;
        }
    },

    renderChart: function(container, data) {
        container.innerHTML = '';

        const history = data.history || [];
        const x = history.map(d => d.oi_chg_pct);
        const y = history.map(d => d.price_chg_pct);
        const text = history.map(d => `${d.time}<br>${d.interpretation}`);
        const color = history.map(d => {
            if (d.interpretation === 'Long Build Up') return '#4caf50'; // Green
            if (d.interpretation === 'Short Covering') return '#00bcd4'; // Blue/Cyan
            if (d.interpretation === 'Short Build Up') return '#f44336'; // Red
            if (d.interpretation === 'Long Unwinding') return '#ff9800'; // Orange
            return '#888';
        });

        const trace = {
            x: x,
            y: y,
            mode: 'markers+text',
            type: 'scatter',
            text: history.map((d, i) => i === history.length - 1 ? 'Latest' : ''),
            textposition: 'top center',
            hovertext: text,
            marker: { size: 12, color: color }
        };

        const layout = {
            title: `Price vs OI Quadrant: ${data.symbol}`,
            paper_bgcolor: '#1a1a1a',
            plot_bgcolor: '#1a1a1a',
            font: { color: '#ccc' },
            xaxis: {
                title: 'OI Change %',
                zeroline: true,
                zerolinecolor: '#444',
                gridcolor: '#333'
            },
            yaxis: {
                title: 'Price Change %',
                zeroline: true,
                zerolinecolor: '#444',
                gridcolor: '#333'
            },
            shapes: [
                // Background Colors for Quadrants (Optional/Subtle)
            ],
            annotations: [
                { x: 2, y: 2, text: 'Long Build Up', showarrow: false, font: {color: '#4caf50'} },
                { x: -2, y: 2, text: 'Short Covering', showarrow: false, font: {color: '#00bcd4'} },
                { x: 2, y: -2, text: 'Short Build Up', showarrow: false, font: {color: '#f44336'} },
                { x: -2, y: -2, text: 'Long Unwinding', showarrow: false, font: {color: '#ff9800'} }
            ]
        };

        Plotly.newPlot(container, [trace], layout, {responsive: true});
    },

    handleTick: function(tick) {
        // Update if active
    }
};

// Register with WorkbookManager
window.addEventListener('load', () => {
   if (window.WorkbookManager) {
       window.WorkbookManager.modules['oi'] = OiTool;
   }
});
