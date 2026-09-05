import re

file_path = "backend/ui/static/js/script_workbench2.js"
with open(file_path, "r") as f:
    content = f.read()

old_init = """        document.addEventListener('DOMContentLoaded', () => {
            switchDerivTab('matrix');
        });"""

new_init = """        document.addEventListener('DOMContentLoaded', () => {
            const lastMainTab = localStorage.getItem('activeWorkbenchTab') || 'terminal';
            switchMainTab(lastMainTab);

            const lastDerivTab = localStorage.getItem('activeDerivTab') || 'matrix';
            switchDerivTab(lastDerivTab);
        });"""

content = content.replace(old_init, new_init)

# Also fix the `if (!document.querySelector('.deriv-sub-tab.active'))` fallback in switchMainTab
old_fallback = """            if (tabName === 'derivatives') {
                // Initialize first sub-tab if none selected
                if (!document.querySelector('.deriv-sub-tab.active')) {
                    switchDerivTab('matrix');
                } else if (document.querySelector('#deriv-tab-matrix').classList.contains('active') && document.getElementById('mr-data-body').innerHTML.includes('No data')) {"""

new_fallback = """            if (tabName === 'derivatives') {
                // Initialize first sub-tab if none selected
                if (!document.querySelector('.deriv-sub-tab.active')) {
                    const lastDerivTab = localStorage.getItem('activeDerivTab') || 'matrix';
                    switchDerivTab(lastDerivTab);
                } else if (document.querySelector('#deriv-tab-matrix') && document.querySelector('#deriv-tab-matrix').classList.contains('active') && document.getElementById('mr-data-body') && document.getElementById('mr-data-body').innerHTML.includes('No data')) {"""

content = content.replace(old_fallback, new_fallback)

with open(file_path, "w") as f:
    f.write(content)
