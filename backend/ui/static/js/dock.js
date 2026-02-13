class DockManager {
    constructor(type, containerId) {
        this.type = type; // 'filters' or 'indicators'
        this.items = [];
        this.container = document.getElementById(containerId);
        this.render();
    }

    // Mock API Fetch - Replace with actual registry fetch later
    async fetchAvailableTools() {
        try {
            const response = await fetch('/strategies/toolbox/registry');
            const data = await response.json();
            // Filter by type if backend supports category filtering
            if (data.tools) {
                // Heuristic: Filters usually have 'Filter' in name or category
                return data.tools.filter(t => {
                    const cat = t.category || '';
                    if (this.type === 'filters') return cat.includes('Filter') || t.name.includes('Filter');
                    if (this.type === 'indicators') return cat.includes('Indicator') || t.name.includes('Skew') || t.name.includes('Pulse');
                    return true;
                });
            }
            return [];
        } catch (e) {
            console.error("Failed to fetch tools", e);
            // Fallback for demo
            return this.type === 'filters'
                ? [{name: 'Z-Score Filter'}, {name: 'ATR Filter'}]
                : [{name: 'Vol Skew'}, {name: 'Sentiment Gauge'}];
        }
    }

    addItem(item) {
        // Prevent duplicates
        if (!this.items.some(i => i.name === item.name)) {
            this.items.push(item);
            this.renderList();
        }
    }

    removeItem(index) {
        this.items.splice(index, 1);
        this.renderList();
    }

    render() {
        if (!this.container) return;
        this.container.innerHTML = `
            <div class="dock-panel">
                <div class="dock-header">
                    <span>Active ${this.type}</span>
                    <span class="dock-count" id="${this.type}-count">0</span>
                </div>
                <ul class="dock-list" id="${this.type}-list"></ul>
                <div class="dock-add-container">
                    <button class="dock-add-btn" id="${this.type}-add-btn">+ Add ${this.type.slice(0,-1)}</button>
                    <div class="dock-dropdown" id="${this.type}-dropdown"></div>
                </div>
            </div>
        `;

        this.bindEvents();
    }

    renderList() {
        const list = document.getElementById(`${this.type}-list`);
        const count = document.getElementById(`${this.type}-count`);

        list.innerHTML = '';
        count.innerText = this.items.length;

        this.items.forEach((item, index) => {
            const li = document.createElement('li');
            li.className = 'dock-item';
            li.innerHTML = `
                <span class="dock-item-label">✅ ${item.name}</span>
                <div class="dock-item-actions">
                    <span class="dock-action-btn" title="Configure">⚙️</span>
                    <span class="dock-action-btn delete" data-index="${index}" title="Remove">🗑️</span>
                </div>
            `;
            list.appendChild(li);
        });

        // Re-bind delete events
        list.querySelectorAll('.delete').forEach(btn => {
            btn.onclick = (e) => {
                this.removeItem(parseInt(e.target.dataset.index));
            }
        });
    }

    bindEvents() {
        const addBtn = document.getElementById(`${this.type}-add-btn`);
        const dropdown = document.getElementById(`${this.type}-dropdown`);

        addBtn.onclick = async () => {
            dropdown.classList.toggle('active');
            if (dropdown.classList.contains('active')) {
                const tools = await this.fetchAvailableTools();
                dropdown.innerHTML = '';
                if (tools.length === 0) {
                    dropdown.innerHTML = '<div class="dock-dropdown-item">No tools found</div>';
                }
                tools.forEach(tool => {
                    const div = document.createElement('div');
                    div.className = 'dock-dropdown-item';
                    div.innerText = tool.name;
                    div.onclick = () => {
                        this.addItem(tool);
                        dropdown.classList.remove('active');
                    };
                    dropdown.appendChild(div);
                });
            }
        };

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (this.container && !this.container.contains(e.target)) {
                dropdown.classList.remove('active');
            }
        });
    }
}
