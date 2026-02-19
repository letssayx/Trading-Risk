const WorkbookManager = {
    activeStrategy: 'turtle', // 'turtle' or 'statarb'
    modules: {}, // { turtle: TurtleTab, statarb: StatArbTab }

    init: function() {
        this.modules = {
            turtle: TurtleTab,
            statarb: StatArbTab,
            'price-oi': PriceOITab,
            rollover: RolloverTab
        };

        // Bind Tab Clicks
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
    },

    switchTab: function(type) {
        this.activeStrategy = type;

        // UI Update
        document.querySelectorAll('.wb-tab').forEach(t => t.classList.remove('active'));
        const tab = document.querySelector(`.wb-tab[data-type="${type}"]`);
        if (tab) tab.classList.add('active');

        // Content Update
        const container = document.getElementById('wb-content-area');
        container.innerHTML = '';
        this.modules[type].render(container);
    },

    handleTick: function(tick) {
        // Forward to all modules or just active?
        // All active strategies should update regardless of view.
        Object.values(this.modules).forEach(m => m.handleTick(tick));
    }
};
