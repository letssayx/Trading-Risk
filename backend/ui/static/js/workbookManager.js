const WorkbookManager = {
    activeStrategy: 'turtle', // 'turtle' or 'statarb'
    modules: {}, // { turtle: TurtleTab, statarb: StatArbTab }

    init: function() {
        this.modules = {
            turtle: TurtleTab,
            statarb: StatArbTab,
            oi_analysis: OiTool,
            rollover: RolloverTool
        };

        // Bind Inner Tab Clicks for Strategy Workbench
        document.querySelectorAll('.wb-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const type = e.target.dataset.type;
                if (type) this.switchTab(type);
            });
        });

        // Init modules
        TurtleTab.init();
        StatArbTab.init();

        this.switchTab('turtle');

        // Render standalone main tabs directly into their containers
        this.modules['oi_analysis'].render(document.getElementById('tab-oi_analysis'));
        this.modules['rollover'].render(document.getElementById('tab-rollover'));
    },

    switchTab: function(type) {
        if(type === 'turtle' || type === 'statarb') {
            this.activeStrategy = type;

            // UI Update for Strategy Workbench
            document.querySelectorAll('.wb-tab').forEach(t => t.classList.remove('active'));
            const tab = document.querySelector(`.wb-tab[data-type="${type}"]`);
            if (tab) tab.classList.add('active');

            // Content Update
            const container = document.getElementById('wb-content-area');
            container.innerHTML = '';
            this.modules[type].render(container);
        }
    },

    handleTick: function(tick) {
        // Forward to all modules or just active?
        // All active strategies should update regardless of view.
        Object.values(this.modules).forEach(m => m.handleTick(tick));
    }
};
