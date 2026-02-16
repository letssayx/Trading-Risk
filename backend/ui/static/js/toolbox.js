// Toolbox Component
// Handles population of draggable items and drag-start events.

document.addEventListener('DOMContentLoaded', () => {
    const toolboxContent = document.getElementById('toolbox-content');

    // Mock Registry Data
    const registry = {
        "Strategies": ["Turtle", "StatArb", "VolArb", "MeanReversion"],
        "Filters": ["ZScore", "RSI", "ADX", "MaCross"],
        "Indicators": ["SMA", "EMA", "Bollinger", "ATR"],
        "Risk": ["VaR", "ExpShortfall", "Kelly"],
        "Stats": ["Cointegration", "Stationarity", "Hurst"]
    };

    function renderToolbox() {
        if (!toolboxContent) return;

        let html = '';
        for (const [category, items] of Object.entries(registry)) {
            html += `<div style="margin-bottom:10px;">`;
            html += `<div style="color:#888; font-size:0.75em; font-weight:bold; margin-bottom:4px; text-transform:uppercase;">${category}</div>`;
            items.forEach(item => {
                html += `<div class="toolbox-item" draggable="true" data-type="${category}" data-name="${item}">${item}</div>`;
            });
            html += `</div>`;
        }
        toolboxContent.innerHTML = html;

        // Attach Drag Events
        document.querySelectorAll('.toolbox-item').forEach(el => {
            el.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('type', el.dataset.type);
                e.dataTransfer.setData('name', el.dataset.name);
                e.dataTransfer.effectAllowed = 'copy';
            });
        });

        // Setup Drop Zone on Workbook
        const wbPanel = document.getElementById('workbook-panel');
        if(wbPanel) {
            wbPanel.addEventListener('dragover', (e) => e.preventDefault());
            wbPanel.addEventListener('drop', (e) => {
                e.preventDefault();
                const type = e.dataTransfer.getData('type');
                const name = e.dataTransfer.getData('name');

                if (type === 'Strategies') {
                    // Switch to relevant workbook and open add tab
                    if (name === 'Turtle') {
                        window.wbManager.switchWorkbook('TURTLE');
                        window.wbManager.addTab();
                    } else if (name === 'StatArb') {
                        window.wbManager.switchWorkbook('STATARB');
                        window.wbManager.addTab();
                    }
                }
            });
        }
    }

    renderToolbox();
});

// Exposed toggle function
window.toggleToolbox = function() {
    const panel = document.getElementById('toolbox-panel');
    const btn = document.getElementById('toolbox-toggle-btn');
    const splitter = document.getElementById('split-left-internal');

    if (panel.style.width === '0px' || panel.style.width === '') {
        // Open
        panel.style.width = '200px'; // Default open width
        btn.innerText = '«';
        if(splitter) splitter.style.display = 'block';
    } else {
        // Close
        panel.style.width = '0px';
        btn.innerText = '»';
        if(splitter) splitter.style.display = 'none';
    }
};
