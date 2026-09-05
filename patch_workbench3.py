import re

file_path = "backend/ui/static/js/script_workbench2.js"
with open(file_path, "r") as f:
    content = f.read()

# Add localStorage support to switchMainTab
old_switchMainTab = """        function switchMainTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.main-tab-content').forEach(el => el.classList.remove('active'));"""

new_switchMainTab = """        function switchMainTab(tabName) {
            localStorage.setItem('activeWorkbenchTab', tabName);
            // Hide all tabs
            document.querySelectorAll('.main-tab-content').forEach(el => el.classList.remove('active'));"""

content = content.replace(old_switchMainTab, new_switchMainTab)

# Check DOMContentLoaded inside script_workbench2.js
old_init = """        window.marketWatchDataCache = null; // Store fetched Market Watch data globally

        // Initialize tabs based on URL hash if present
        if (window.location.hash) {"""

new_init = """        window.marketWatchDataCache = null; // Store fetched Market Watch data globally

        // Initialize tabs based on localStorage
        const lastTab = localStorage.getItem('activeWorkbenchTab') || 'terminal';
        setTimeout(() => switchMainTab(lastTab), 10);

        // Initialize tabs based on URL hash if present
        if (window.location.hash) {"""

content = content.replace(old_init, new_init)


# Sub tabs: switchDerivTab
old_switchDeriv = """        function switchDerivTab(tabName) {
            document.querySelectorAll('.deriv-sub-tab').forEach(el => el.style.display = 'none');"""

new_switchDeriv = """        function switchDerivTab(tabName) {
            localStorage.setItem('activeDerivTab', tabName);
            document.querySelectorAll('.deriv-sub-tab').forEach(el => el.style.display = 'none');"""

content = content.replace(old_switchDeriv, new_switchDeriv)

with open(file_path, "w") as f:
    f.write(content)
