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
            // Provide specific options instead of generic prompt if possible
            const strategyType = prompt("Select Strategy (turtle/statarb/oi/rollover):", "turtle");
            if (strategyType) WorkbookManager.switchTab(strategyType.toLowerCase());
        } else if (type === 'indicator') {
            const indicatorType = prompt("Select Indicator (SMA/RSI/MACD):", "SMA");
            if (indicatorType) alert(`Indicator ${indicatorType} added (Mock)`);
        } else if (type === 'filter') {
            const filterType = prompt("Select Filter (ZScore/ADX/Regime):", "ZScore");
            if (filterType) alert(`Filter ${filterType} applied (Mock)`);
        } else if (type === 'risk') {
             const riskType = prompt("Select Risk Model (VaR/Euler/Kelly):", "VaR");
             if (riskType) alert(`Risk Model ${riskType} activated (Mock)`);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => Toolbox.init());
