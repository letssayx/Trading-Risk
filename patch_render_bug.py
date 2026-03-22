import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Replace the incorrect event listener at the very end
bad_listener = """document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('div-symbol-search');
    if (searchInput) {
        searchInput.addEventListener('input', renderDividendsData);
    }
});"""

if bad_listener in content:
    content = content.replace(bad_listener, """// Removed incorrect input event listener that broke Enter key logic
document.addEventListener('DOMContentLoaded', () => {
    // Other DOMContentLoaded logic if needed
});""")
    with open('backend/ui/templates/workbench.html', 'w') as f:
        f.write(content)
    print("Patched workbench.html successfully (removed incorrect input listener).")
else:
    print("Could not find the target string to replace.")
