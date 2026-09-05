import re

file_path = "backend/ui/templates/derivatives.html"
with open(file_path, "r") as f:
    content = f.read()


old_switch = """        function switchClientTab(tabId) {
            document.querySelectorAll('.client-tab-content').forEach(el => el.classList.remove('active'));"""

new_switch = """        function switchClientTab(tabId) {
            localStorage.setItem('activeDerivativesTab', tabId);
            document.querySelectorAll('.client-tab-content').forEach(el => el.classList.remove('active'));"""

content = content.replace(old_switch, new_switch)


old_init = """    <script>
        document.addEventListener('DOMContentLoaded', () => {
            // Initialize workbook modules so their render() functions work
            if (typeof WorkbookManager !== 'undefined') {
                WorkbookManager.init();
            }

            // Switch to AI tab by default
            switchClientTab('ai');
        });
    </script>"""

new_init = """    <script>
        document.addEventListener('DOMContentLoaded', () => {
            // Initialize workbook modules so their render() functions work
            if (typeof WorkbookManager !== 'undefined') {
                WorkbookManager.init();
            }

            // Switch to last active tab or AI tab by default
            const lastTab = localStorage.getItem('activeDerivativesTab') || 'ai';
            switchClientTab(lastTab);
        });
    </script>"""

content = content.replace(old_init, new_init)

with open(file_path, "w") as f:
    f.write(content)
