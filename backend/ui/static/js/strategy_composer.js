class StrategyComposer {
    constructor() {
        this.canvas = document.getElementById('composer-canvas');
        this.svgLayer = document.getElementById('connections-layer');
        this.nodes = [];
        this.draggedNode = null;
        this.isDragging = false;

        this.init();

        // Expose to window for Jules Chat
        window.strategyComposer = this;
    }

    init() {
        if (!this.canvas) return;
        this.initDragDrop();

        // Toolbar Actions
        const saveBtn = document.getElementById('save-strategy-btn');
        if (saveBtn) saveBtn.onclick = () => this.saveStrategy();

        const backtestBtn = document.getElementById('backtest-btn');
        if (backtestBtn) backtestBtn.onclick = () => this.runBacktest();
    }

    initDragDrop() {
        // Palette Items
        document.querySelectorAll('.palette-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('type', item.dataset.type);
                e.dataTransfer.setData('name', item.innerText);
            });
        });

        // Canvas Drop
        this.canvas.addEventListener('dragover', (e) => e.preventDefault());
        this.canvas.addEventListener('drop', (e) => {
            e.preventDefault();
            const type = e.dataTransfer.getData('type');
            const name = e.dataTransfer.getData('name');
            const x = e.offsetX;
            const y = e.offsetY;
            this.createNode(type, name, x, y);
        });
    }

    createNode(type, name, x, y, params={}) {
        const node = document.createElement('div');
        node.className = 'node';
        node.style.left = x + 'px';
        node.style.top = y + 'px';

        const id = 'node_' + Date.now() + Math.random().toString(36).substr(2, 5);
        node.id = id;

        node.innerHTML = `
            <div class="node-header">
                <span>${name}</span>
                <span style="cursor:pointer;" onclick="this.closest('.node').remove()">✕</span>
            </div>
            <div class="node-body">
                <small>${type.toUpperCase()}</small>
                ${this.getNodeControls(type, params)}
            </div>
            <div class="node-ports">
                <div class="port input" title="Input"></div>
                <div class="port output" title="Output"></div>
            </div>
        `;

        this.makeDraggable(node);
        this.canvas.appendChild(node);
        this.nodes.push({ id, type, name, el: node });
        return id;
    }

    getNodeControls(type, params) {
        if (type === 'filter') {
            const val = params.window || params.period || 14;
            return `<div style="margin-top:5px;">Param: <input type="number" style="width:40px" value="${val}"></div>`;
        }
        if (type === 'logic') return '<div style="margin-top:5px;"><select><option>AND</option><option>OR</option></select></div>';
        return '';
    }

    makeDraggable(el) {
        let isDown = false;
        let offset = [0,0];

        const header = el.querySelector('.node-header');
        header.addEventListener('mousedown', (e) => {
            isDown = true;
            offset = [
                el.offsetLeft - e.clientX,
                el.offsetTop - e.clientY
            ];
        }, true);

        document.addEventListener('mouseup', () => isDown = false, true);

        document.addEventListener('mousemove', (e) => {
            if (isDown) {
                e.preventDefault();
                el.style.left = (e.clientX + offset[0]) + 'px';
                el.style.top  = (e.clientY + offset[1]) + 'px';
                // TODO: Update connections
            }
        }, true);
    }

    saveStrategy() {
        const name = prompt("Enter Strategy Name:");
        if (name) {
            console.log("Saving Strategy:", name, this.nodes);
            alert(`Strategy "${name}" saved!`);
        }
    }

    runBacktest() {
        alert("Running Backtest on current composition...");
        console.log("Backtesting nodes:", this.nodes);
    }

    // API: Load from Parser Config
    loadFromCode(config) {
        if (!config) return;

        // Clear canvas
        this.nodes.forEach(n => n.el.remove());
        this.nodes = [];

        let x = 50;
        let y = 50;

        // 1. Create Strategy Node
        if (config.strategy) {
            this.createNode('strategy', config.strategy.toUpperCase(), x, y, config.params);
            y += 120;
        }

        // 2. Create Filters
        if (config.filters) {
            config.filters.forEach(f => {
                this.createNode('filter', f.type.toUpperCase(), x, y, f);
                y += 120;
            });
        }

        // 3. Create Risk
        if (config.risk) {
            config.risk.forEach(r => {
                this.createNode('risk', r.type.toUpperCase(), x, y, r);
                y += 120;
            });
        }

        // Switch to Strategy Tab to show user
        const tabBtn = document.querySelector("button[onclick=\"switchTab('strategy')\"]");
        if (tabBtn) tabBtn.click();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Only init if not already done (window.onload conflict safety)
    if (!window.strategyComposer) {
        new StrategyComposer();
    }
});
