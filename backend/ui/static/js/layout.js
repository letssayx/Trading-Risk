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

            // Global Shortcuts
            if (e.altKey && !e.ctrlKey && !e.shiftKey) {
                switch(e.code) {
                    case 'KeyH': // Alt+H: Historical Data
                        e.preventDefault();
                        if (typeof switchMainTab === 'function') switchMainTab('history');
                        else window.location.href = '/data-viewer';
                        break;
                    case 'KeyI': // Alt+I: Import Data
                        e.preventDefault();
                        if (typeof switchMainTab === 'function') switchMainTab('import');
                        else if (window.uploader) window.uploader.open();
                        break;
                    case 'KeyA': // Alt+A: AI-Analyze
                        e.preventDefault();
                        if (typeof switchMainTab === 'function') switchMainTab('ai_analyze');
                        break;
                    case 'KeyU': // Alt+U: Audit Trail
                        e.preventDefault();
                        if (typeof switchMainTab === 'function') switchMainTab('audit');
                        else {
                            const auditModal = document.getElementById('audit-modal');
                            if (auditModal) auditModal.style.display = 'flex';
                        }
                        break;
                    case 'KeyC': // Alt+C: Config
                        e.preventDefault();
                        if (typeof switchMainTab === 'function') switchMainTab('config');
                        else if (typeof openConfig === 'function') openConfig();
                        else {
                            const configModal = document.getElementById('config-modal');
                            if (configModal) configModal.style.display = 'block';
                        }
                        break;
                    case 'KeyJ': // Alt+J: Jules Chat
                        e.preventDefault();
                        const julesInput = document.getElementById('jules-input');
                        if (julesInput) {
                            if (typeof switchLeftTab === 'function') switchLeftTab('jules');
                            julesInput.focus();
                        }
                        break;
                    case 'KeyP': // Alt+P: Python Code
                        e.preventDefault();
                        if (typeof switchLeftTab === 'function') switchLeftTab('python');
                        break;
                }
            }
        });

        // Fix Close buttons via Event Delegation for dynamically created elements
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.close');
            if (btn) {
                const modal = btn.closest('.modal');
                if (modal) modal.style.display = 'none';
            }
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

// Autocomplete logic for AI Analyze Input
document.addEventListener('DOMContentLoaded', () => {
    const aiInput = document.getElementById('ai-cmd-input');
    const dropdown = document.getElementById('ai-autocomplete-dropdown');

    if (aiInput && dropdown) {
        let timeout = null;

        aiInput.addEventListener('input', (e) => {
            clearTimeout(timeout);
            const val = e.target.value;

            // Extract the last word being typed
            const words = val.split(/[\s,]+/);
            const lastWord = words[words.length - 1];

            if (lastWord.length >= 2) {
                timeout = setTimeout(async () => {
                    try {
                        const res = await fetch(`/api/data/view/symbols/autocomplete?q=${encodeURIComponent(lastWord)}`);
                        if (res.ok) {
                            const matches = await res.json();
                            if (matches.length > 0) {
                                dropdown.innerHTML = '';
                                matches.forEach(match => {
                                    const div = document.createElement('div');
                                    div.style.padding = '8px';
                                    div.style.cursor = 'pointer';
                                    div.style.borderBottom = '1px solid #333';
                                    div.textContent = `${match.symbol} - ${match.name}`;

                                    div.addEventListener('mouseenter', () => div.style.backgroundColor = '#2d2d2d');
                                    div.addEventListener('mouseleave', () => div.style.backgroundColor = 'transparent');

                                    div.addEventListener('click', () => {
                                        // Replace the last word with the selected symbol
                                        const newWords = [...words];
                                        newWords[newWords.length - 1] = match.symbol;
                                        aiInput.value = newWords.join(' ') + ' ';
                                        dropdown.style.display = 'none';
                                        aiInput.focus();
                                    });
                                    dropdown.appendChild(div);
                                });
                                dropdown.style.display = 'block';
                            } else {
                                dropdown.style.display = 'none';
                            }
                        }
                    } catch (error) {
                        console.error('Autocomplete fetch error:', error);
                    }
                }, 300); // 300ms debounce
            } else {
                dropdown.style.display = 'none';
            }
        });

        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target !== aiInput && e.target !== dropdown && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
    }
});
