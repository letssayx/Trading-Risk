import re
with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
    js_content = f.read()

# Fix Special Situation Arb sub-tabs navigation
js_content = re.sub(
    r"function switchArbTab\(tabId\) \{.*?\}",
    """function switchArbTab(tabId) {
    document.querySelectorAll('.ss-sub-tab').forEach(el => el.classList.remove('active'));
    // Do NOT remove .active from .wb-tab globally. We only want to remove it from the arb sub-tab buttons.
    document.querySelectorAll('.wb-tabs-header .wb-tab').forEach(el => {
        // Only target tabs within the arb section if possible, but for now just target all wb-tabs
        // Actually, let's be more specific to avoid breaking the main tabs if they share classes.
        // The arb tabs are in a specific container, but let's just use the IDs we know.
        if (el.id && el.id.startsWith('ss-tab-btn-')) {
            el.classList.remove('active');
        }
    });

    const tabContent = document.getElementById('ss-tab-' + tabId);
    if (tabContent) {
        tabContent.classList.add('active');
    }

    const tabBtn = document.getElementById('ss-tab-btn-' + tabId);
    if (tabBtn) {
        tabBtn.classList.add('active');
    }
}""",
    js_content,
    flags=re.DOTALL
)

with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
    f.write(js_content)
