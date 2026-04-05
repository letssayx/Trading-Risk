const Toolbox = {
    draggedData: null,

    init: function() {
        // Load Strategies dynamically
        this.loadStrategies();

        // Attach listeners to existing static items
        this.attachListeners();
        this.setupDropZones();
    },

    loadStrategies: async function() {
        try {
            const res = await fetch('/api/strategies/list');
            const data = await res.json();
            const container = document.getElementById('strategies-flyout');
            if (!container) return; // Guard
            container.innerHTML = '';

            // Helper to create item
            const createItem = (strat, isUser) => {
                const el = document.createElement('div');
                el.className = 'flyout-item';
                el.draggable = true;
                el.dataset.type = 'strategy';
                el.dataset.name = strat.name;
                el.title = `${strat.description}`;

                // Cleanup Name: Remove 'Strategy', 'Legacy', 'Analyzer' from display
                let displayName = strat.name
                    .replace('Legacy', '')
                    .replace('Strategy', '')
                    .replace('Analyzer', '')
                    .replace(/([A-Z])/g, ' $1').trim(); // Add spaces

                // Content
                const icon = isUser ? '👤' : '♟️';
                el.innerHTML = `
                    <div class="flyout-item-icon" style="color:${isUser ? '#ff9800' : '#60a5fa'}">${icon}</div>
                    <div class="flyout-item-name">${displayName}</div>
                `;

                // Attach drag start directly
                el.addEventListener('dragstart', (e) => {
                    const payload = JSON.stringify({
                        type: 'strategy',
                        name: strat.name,
                        isUser: isUser
                    });
                    e.dataTransfer.setData('application/json', payload);
                    e.dataTransfer.effectAllowed = 'copy';
                    this.draggedData = payload;
                });

                // Attach Click to Open
                el.addEventListener('click', () => {
                     this.handleOpenStrategy(strat.name);
                });

                return el;
            };

            // OOTB
            if (data.ootb && data.ootb.length > 0) {
                const header = document.createElement('div');
                header.className = 'flyout-header';
                header.innerText = 'BUILT-IN';
                container.appendChild(header);

                data.ootb.forEach(s => container.appendChild(createItem(s, false)));
            }

            // User
            if (data.user && data.user.length > 0) {
                const header = document.createElement('div');
                header.className = 'flyout-header';
                header.style.marginTop = '10px';
                header.innerText = 'USER';
                container.appendChild(header);

                data.user.forEach(s => container.appendChild(createItem(s, true)));
            }

        } catch (e) {
            console.error("Failed to load strategies", e);
            const container = document.getElementById('strategies-flyout');
            if (container) container.innerHTML = '<div style="color:red; font-size:10px;">Err</div>';
        }
    },

    attachListeners: function() {
        // For static items (Filters, Indicators, etc.)
        const items = document.querySelectorAll('.toolbox-item:not(.strategy-item)');
        items.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                const payload = JSON.stringify({
                    type: item.dataset.type,
                    name: item.title // Fallback name
                });
                e.dataTransfer.setData('application/json', payload);
                e.dataTransfer.effectAllowed = 'copy';
                this.draggedData = payload;
            });
        });
    },

    setupDropZones: function() {
        // Drop on Chart
        const chartArea = document.getElementById('chart-workbench');
        chartArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            chartArea.style.border = '2px dashed #60a5fa';
        });
        chartArea.addEventListener('dragleave', () => chartArea.style.border = 'none');
        chartArea.addEventListener('drop', (e) => {
            e.preventDefault();
            chartArea.style.border = 'none';
            this.handleDrop(e, 'chart');
        });

        // Drop on Workbook
        const workbookArea = document.getElementById('strategy-workbench');
        workbookArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            workbookArea.style.border = '2px dashed #60a5fa';
        });
        workbookArea.addEventListener('dragleave', () => workbookArea.style.border = 'none');
        workbookArea.addEventListener('drop', (e) => {
            e.preventDefault();
            workbookArea.style.border = 'none';
            this.handleDrop(e, 'workbook');
        });
    },

    handleDrop: function(e, targetZone) {
        let data = null;
        try {
            const json = e.dataTransfer.getData('application/json');
            data = JSON.parse(json);
        } catch (err) {
            // Fallback for simple text/plain if any
            const type = e.dataTransfer.getData('text/plain');
            if (type) data = { type: type };
        }

        if (!data && this.draggedData) {
             try { data = JSON.parse(this.draggedData); } catch(e){}
        }

        if (!data) return;

        if (targetZone === 'chart') {
            this.handleDropOnChart(data);
        } else {
            this.handleDropOnWorkbook(data);
        }
    },

    handleOpenStrategy: function(strategyName) {
        // Map known strategies to tabs, or default
        // TurtleLegacyStrategy -> turtle
        // StatArbAlphaEngine -> statarb
        let tabType = 'turtle';
        const lower = strategyName.toLowerCase();

        if (lower.includes('turtle')) tabType = 'turtle';
        else if (lower.includes('stat') && lower.includes('arb')) tabType = 'statarb';
        else if (lower.includes('oi') && lower.includes('price')) tabType = 'oi'; // PriceOiAnalyzer
        else if (lower.includes('rollover')) tabType = 'rollover'; // RolloverAnalyzer
        else {
             // For unknown/user strategies, maybe alert or open a generic tab
             alert(`Opening User Strategy: ${strategyName}`);
             return;
        }

        WorkbookManager.switchTab(tabType);
    },

    handleDropOnChart: function(data) {
        if (data.type === 'indicator') {
            alert('Indicator added to active chart (Mock)');
        } else {
            console.log(`Dropped ${data.type} on chart - no action`);
        }
    },

    handleDropOnWorkbook: function(data) {
        if (data.type === 'strategy') {
            this.handleOpenStrategy(data.name);

        } else if (data.type === 'indicator') {
            const indicatorType = prompt("Select Indicator (SMA/RSI/MACD):", "SMA");
            if (indicatorType) alert(`Indicator ${indicatorType} added (Mock)`);
        } else if (data.type === 'filter') {
            const filterType = prompt("Select Filter (ZScore/ADX/Regime):", "ZScore");
            if (filterType) alert(`Filter ${filterType} applied (Mock)`);
        } else if (data.type === 'risk') {
             const riskType = prompt("Select Risk Model (VaR/Euler/Kelly):", "VaR");
             if (riskType) alert(`Risk Model ${riskType} activated (Mock)`);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => Toolbox.init());
