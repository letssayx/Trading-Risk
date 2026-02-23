const Layout = {
    init: function() {
        this.initResizers();
        this.setupGlobalEvents();
        this.setupAuditInterceptors();
    },

    setupAuditInterceptors: function() {
        // Capture Clicks on Buttons/Tabs
        document.addEventListener('click', (e) => {
            const target = e.target.closest('button, .tab-btn, .toolbox-item');
            if (target) {
                const action = target.innerText || target.title || target.id;
                this.logAction('Click', `User clicked ${action}`, { id: target.id, class: target.className });
            }
        });
    },

    logAction: async function(eventType, message, meta = {}) {
        try {
            await fetch('/api/audit/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    level: 'USER',
                    source: 'Frontend',
                    event_type: eventType,
                    message: message,
                    meta_data: meta
                })
            });
        } catch (e) {
            // console.warn("Failed to send audit log", e);
        }
    },

    setupGlobalEvents: function() {
        // Global Escape Handler to close Modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.modal');
                modals.forEach(m => m.style.display = 'none');
            }
        });

        // Fix Close buttons
        const closeBtns = document.querySelectorAll('.close');
        closeBtns.forEach(btn => {
            btn.onclick = function() {
                const modal = this.closest('.modal');
                if (modal) modal.style.display = 'none';
            };
        });
    },

    initResizers: function() {
        // Vertical Resizer (Left Panel)
        const leftPanel = document.getElementById('left-panel');
        const resizerLeft = document.getElementById('resizer-left');

        if (resizerLeft) {
            resizerLeft.addEventListener('mousedown', (e) => {
                e.preventDefault();
                document.addEventListener('mousemove', resizeLeft);
                document.addEventListener('mouseup', stopResizeLeft);
            });

            function resizeLeft(e) {
                leftPanel.style.width = e.clientX - 50 + 'px'; // Minus toolbox width
            }
            function stopResizeLeft() {
                document.removeEventListener('mousemove', resizeLeft);
                document.removeEventListener('mouseup', stopResizeLeft);
            }
        }

        // Horizontal Resizer (Charts vs Workbook)
        const chartBox = document.getElementById('chart-workbench');
        const resizerCharts = document.getElementById('resizer-charts');

        if (resizerCharts) {
            resizerCharts.addEventListener('mousedown', (e) => {
                e.preventDefault();
                document.addEventListener('mousemove', resizeHeight);
                document.addEventListener('mouseup', stopResizeHeight);
            });

            function resizeHeight(e) {
                // e.clientY is relative to viewport.
                // We need relative to main-panel, but main-panel starts at top.
                // Chart box height is effectively e.clientY.
                chartBox.style.height = e.clientY + 'px';

                // Notify charts to resize
                if (window.ChartTabs) ChartTabs.resizeAll();
            }
            function stopResizeHeight() {
                document.removeEventListener('mousemove', resizeHeight);
                document.removeEventListener('mouseup', stopResizeHeight);
            }
        }
    }
};
