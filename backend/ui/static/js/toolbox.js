const Toolbox = {
    tools: [],
    drawer: null,
    drawerContent: null,
    drawerTitle: null,

    // Category Mappings (UI -> Backend Categories)
    categoryMap: {
        'Strategy': ['Strategy', 'Strategies'],
        'Filter': ['Filter', 'Filters', 'Stats'],
        'Indicator': ['Analysis', 'Math', 'Ingest'],
        'Risk': ['Risk', 'Governance']
    },

    init: async function() {
        console.log("Toolbox Initializing...");
        this.drawer = document.getElementById('toolbox-drawer');
        this.drawerContent = document.getElementById('drawer-content');
        this.drawerTitle = document.getElementById('drawer-title');

        // Fetch tools
        try {
            const res = await fetch('/strategies/toolbox/registry');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            this.tools = data.tools || [];
            console.log(`Toolbox: Loaded ${this.tools.length} tools.`);
        } catch(e) {
            console.error("Toolbox: Failed to fetch tools", e);
        }

        // Bind clicks
        document.querySelectorAll('.toolbox-item').forEach(item => {
            item.addEventListener('click', () => {
                const cat = item.dataset.category;
                this.openDrawer(cat);
            });
            // Disable native drag on the category icon itself if we want them to click first
            // Or allow dragging generic type? User asked to "click ... show available".
            // So click behavior is prioritized.
            item.draggable = false;
        });

        // Close drawer on outside click (if not on toolbox)
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#toolbox') && !e.target.closest('#toolbox-drawer')) {
                this.closeDrawer();
            }
        });
    },

    openDrawer: function(uiCategory) {
        if (!this.drawer) return;

        // Filter tools
        const validCats = this.categoryMap[uiCategory] || [uiCategory];
        const filteredTools = this.tools.filter(t =>
            validCats.some(c => t.category.includes(c))
        );

        this.drawerTitle.innerText = uiCategory;
        this.drawerContent.innerHTML = '';

        if (filteredTools.length === 0) {
            this.drawerContent.innerHTML = '<div style="color:#888; padding:10px;">No tools found.</div>';
        } else {
            filteredTools.forEach(tool => {
                const el = document.createElement('div');
                el.className = 'tool-card';
                el.draggable = true;
                el.innerHTML = `
                    <div class="tool-title">${tool.name}</div>
                    <div class="tool-desc">${tool.description}</div>
                `;

                el.addEventListener('dragstart', (e) => {
                    e.dataTransfer.setData('application/json', JSON.stringify(tool));
                    e.dataTransfer.effectAllowed = 'copy';
                });

                this.drawerContent.appendChild(el);
            });
        }

        this.drawer.style.display = 'flex';
        // Position it: handled by CSS (absolute to left panel container?)
        // Actually CSS sets it relative to #app-container? No, it's inside #app-container?
        // Wait, #toolbox-drawer is after #toolbox. #app-container is flex.
        // #toolbox is position relative? No.
        // I put #toolbox-drawer as a sibling of #toolbox.
        // To make it appear *over* the left panel, I need absolute positioning relative to #app-container or body.
        // CSS: left: 50px (toolbox width). top: 30px.
    },

    closeDrawer: function() {
        if (this.drawer) this.drawer.style.display = 'none';
    }
};

document.addEventListener('DOMContentLoaded', () => Toolbox.init());
