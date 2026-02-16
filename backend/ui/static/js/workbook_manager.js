class WorkbookManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.activeWorkbook = 'TURTLE'; // Default
        this.workbooks = {
            'TURTLE': { tabs: [], nextId: 1 },
            'STATARB': { tabs: [], nextId: 1 }
        };

        this.renderShell();
        this.switchWorkbook('TURTLE');
    }

    renderShell() {
        this.container.innerHTML = `
            <div class="workbook-tabs" id="wb-top-tabs">
                <div class="wb-tab active" onclick="window.wbManager.switchWorkbook('TURTLE')">TURTLE (Single)</div>
                <div class="wb-tab" onclick="window.wbManager.switchWorkbook('STATARB')">STATARB (Pairs)</div>
                <div class="wb-tab-add">+</div>
            </div>
            <div class="workbook-toolbar" id="wb-toolbar">
                <button class="wb-btn" onclick="window.wbManager.addTab()">+ Add Symbol</button>
            </div>
            <div id="wb-inner-tabs" class="workbook-tabs" style="background:#202020; border-bottom:1px solid #333; font-size:0.75em;">
                <!-- Inner Tabs (Symbols) -->
            </div>
            <div id="wb-content" style="flex:1; overflow:auto;">
                <!-- Tab Content -->
            </div>
        `;
    }

    switchWorkbook(type) {
        this.activeWorkbook = type;

        // Update Top Tabs UI
        const tabs = document.querySelectorAll('#wb-top-tabs .wb-tab');
        tabs.forEach(t => {
            if (t.innerText.includes(type)) t.classList.add('active');
            else t.classList.remove('active');
        });

        // Update Toolbar Text
        const addBtn = document.querySelector('#wb-toolbar button');
        addBtn.innerText = type === 'TURTLE' ? '+ Add Symbol' : '+ Add Pair';

        this.renderInnerTabs();

        // Render Active Inner Tab Content if exists
        const activeTab = this.workbooks[type].tabs.find(t => t.active);
        if (activeTab) {
            this.renderTabContent(activeTab);
        } else {
            document.getElementById('wb-content').innerHTML = '<div style="padding:20px; color:#666;">No active tabs. Add one to start.</div>';
        }
    }

    addTab() {
        const type = this.activeWorkbook;

        if (type === 'TURTLE') {
            window.symbolSearch.open((sym) => {
                const newTab = { id: Date.now(), symbol: sym.toUpperCase(), type: 'TURTLE', active: true };
                this.workbooks.TURTLE.tabs.forEach(t => t.active = false);
                this.workbooks.TURTLE.tabs.push(newTab);
                this.switchWorkbook('TURTLE');
            });

        } else if (type === 'STATARB') {
            // For StatArb, we need 2 symbols. For MVP, just prompt twice or custom modal later.
            // Using prompts as placeholder for multi-select modal
            const sym1 = prompt("Enter Symbol 1:", "NIFTY");
            if(!sym1) return;
            const sym2 = prompt("Enter Symbol 2:", "BANKNIFTY");
            if (!sym2) return;

            const newTab = { id: Date.now(), sym1: sym1.toUpperCase(), sym2: sym2.toUpperCase(), type: 'STATARB', active: true };
            this.workbooks.STATARB.tabs.forEach(t => t.active = false);
            this.workbooks.STATARB.tabs.push(newTab);
            this.switchWorkbook('STATARB');
        }
    }

    renderInnerTabs() {
        const container = document.getElementById('wb-inner-tabs');
        let html = '';

        this.workbooks[this.activeWorkbook].tabs.forEach(tab => {
            const label = tab.type === 'TURTLE' ? tab.symbol : `${tab.sym1}/${tab.sym2}`;
            const activeClass = tab.active ? 'active' : '';
            html += `<div class="wb-tab ${activeClass}" onclick="window.wbManager.selectTab(${tab.id})">${label} <span onclick="window.wbManager.closeTab(${tab.id}, event)">x</span></div>`;
        });

        container.innerHTML = html;
    }

    selectTab(id) {
        this.workbooks[this.activeWorkbook].tabs.forEach(t => t.active = (t.id === id));
        this.switchWorkbook(this.activeWorkbook); // Re-render
    }

    closeTab(id, event) {
        event.stopPropagation();
        const wb = this.workbooks[this.activeWorkbook];
        wb.tabs = wb.tabs.filter(t => t.id !== id);
        if (wb.tabs.length > 0) wb.tabs[0].active = true;
        this.switchWorkbook(this.activeWorkbook);
    }

    renderTabContent(tab) {
        const container = document.getElementById('wb-content');
        container.innerHTML = ''; // Clear

        if (tab.type === 'TURTLE') {
            if (!window.TurtleTab) return;
            new window.TurtleTab(container, tab);
        } else {
            if (!window.StatArbTab) return;
            new window.StatArbTab(container, tab);
        }
    }

    openChart(title) {
        if(window.chartTabs) {
            window.chartTabs.addTab(title);
        }
    }

    async startStrategy(symbol, type) {
        // Send request to backend to initialize adapter
        try {
            const url = type === 'TURTLE' ? '/api/strategies/turtle/start' : '/api/strategies/statarb/start';
            const body = type === 'TURTLE'
                ? { symbol: symbol, windowSize: 20 }
                : { symbol1: symbol.split('/')[0], symbol2: symbol.split('/')[1] || 'BANKNIFTY' }; // Simplistic parsing

            const res = await fetch(url, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body)
            });
            const data = await res.json();
            alert(`Strategy Started: ${data.instanceId}`);

            // Mark tab as active/engine on (logic to update tab state)
            const wb = this.workbooks[type];
            const tab = wb.tabs.find(t => t.symbol === symbol || (t.sym1 + '/' + t.sym2) === symbol);
            if(tab) {
                tab.engineActive = true;
                this.renderTabContent(tab); // Re-render to show status
            }

        } catch(e) {
            console.error("Start Strategy Error", e);
            alert("Failed to start strategy engine.");
        }
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    window.wbManager = new WorkbookManager('workbook-panel');
});
