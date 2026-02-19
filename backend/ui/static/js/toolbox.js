const Toolbox = {
    draggedType: null,

    init: function() {
        const items = document.querySelectorAll('.toolbox-item');
        items.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                this.draggedType = e.target.dataset.type;
                e.dataTransfer.setData('text/plain', this.draggedType);
                e.dataTransfer.effectAllowed = 'copy';
            });
        });

        this.setupDropZones();
    },

    setupDropZones: function() {
        // Drop on Chart
        const chartArea = document.getElementById('chart-workbench');
        chartArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            chartArea.style.border = '2px dashed #00bcd4';
        });
        chartArea.addEventListener('dragleave', () => chartArea.style.border = 'none');
        chartArea.addEventListener('drop', (e) => {
            e.preventDefault();
            chartArea.style.border = 'none';
            const type = e.dataTransfer.getData('text/plain');
            this.handleDropOnChart(type);
        });

        // Drop on Workbook
        const workbookArea = document.getElementById('strategy-workbench');
        workbookArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            workbookArea.style.border = '2px dashed #00bcd4';
        });
        workbookArea.addEventListener('dragleave', () => workbookArea.style.border = 'none');
        workbookArea.addEventListener('drop', (e) => {
            e.preventDefault();
            workbookArea.style.border = 'none';
            const type = e.dataTransfer.getData('text/plain');
            this.handleDropOnWorkbook(type);
        });
    },

    handleDropOnChart: function(type) {
        if (type === 'indicator') {
            // Mock adding indicator
            alert('Indicator added to active chart (Mock)');
            // In real app, call ChartTabs.addIndicator()
        } else {
            console.log(`Dropped ${type} on chart - no action`);
        }
    },

    handleDropOnWorkbook: function(type) {
        if (type === 'strategy') {
            // Prompt to add new strategy instance
            const strategyType = prompt("Select Strategy (turtle/statarb/oi/rollover):", "turtle");
            if (strategyType === 'turtle') {
                WorkbookManager.switchTab('turtle');
            } else if (strategyType === 'statarb') {
                WorkbookManager.switchTab('statarb');
            } else if (strategyType === 'oi') {
                WorkbookManager.switchTab('oi');
            } else if (strategyType === 'rollover') {
                WorkbookManager.switchTab('rollover');
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => Toolbox.init());
