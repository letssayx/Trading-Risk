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
        const oiContainer = document.getElementById('oi-tool-container');
        if (oiContainer && !oiContainer.innerHTML.includes('oi-symbol')) {
            this.modules['oi_analysis'].render(oiContainer);
        }

        const rolloverContainer = document.getElementById('deriv-tab-rollover');
        if (rolloverContainer) {
            this.modules['rollover'].render(rolloverContainer);
        }
    },

    switchTab: function(type) {
        if(type === 'turtle' || type === 'statarb') {
            this.activeStrategy = type;

            // UI Update for Strategy Workbench
            document.querySelectorAll('.wb-tab').forEach(t => t.classList.remove('active'));
            const tab = document.querySelector(`.wb-tab[data-type="${type}"]`);
            if (tab) tab.classList.add('active');

            // Content Update - toggle visibility instead of clearing innerHTML
            // We assume there are sub-containers for each strategy
            const container = document.getElementById('wb-content-area');

            // Check if strategy containers exist, create if not
            let turtleContainer = document.getElementById('turtle-strategy-container');
            let statarbContainer = document.getElementById('statarb-strategy-container');

            if (!turtleContainer) {
                turtleContainer = document.createElement('div');
                turtleContainer.id = 'turtle-strategy-container';
                turtleContainer.style.height = '100%';
                container.appendChild(turtleContainer);
                this.modules['turtle'].render(turtleContainer);
            }
            if (!statarbContainer) {
                statarbContainer = document.createElement('div');
                statarbContainer.id = 'statarb-strategy-container';
                statarbContainer.style.height = '100%';
                container.appendChild(statarbContainer);
                this.modules['statarb'].render(statarbContainer);
            }

            // Toggle Display
            if (type === 'turtle') {
                turtleContainer.style.display = 'block';
                statarbContainer.style.display = 'none';
            } else if (type === 'statarb') {
                turtleContainer.style.display = 'none';
                statarbContainer.style.display = 'block';
            }

            // Re-render ECharts or resize them since they might have collapsed while hidden
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 10);
        }
    },

    handleTick: function(tick) {
        // Forward to all modules or just active?
        // All active strategies should update regardless of view.
        Object.values(this.modules).forEach(m => m.handleTick(tick));
    }
};
