import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# We need to make sure that searchInput triggers loadDividendsData when Enter is pressed!
# Currently `setupAutocomplete('div-symbol-search')` SHOULD do this if we type into it, but if we don't use autocomplete...
# Let's add an explicit keydown listener for Enter on the div-symbol-search input.

new_listener = """document.addEventListener('DOMContentLoaded', () => {
    // Other DOMContentLoaded logic if needed
    const searchInput = document.getElementById('div-symbol-search');
    if (searchInput) {
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (typeof loadDividendsData === 'function') {
                    loadDividendsData();
                }
            }
        });
    }
});"""

content = content.replace("""// Removed incorrect input event listener that broke Enter key logic
document.addEventListener('DOMContentLoaded', () => {
    // Other DOMContentLoaded logic if needed
});""", new_listener)

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
print("Added explicit Enter key listener to div-symbol-search.")
