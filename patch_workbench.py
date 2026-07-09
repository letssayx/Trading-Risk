import re

with open("backend/ui/templates/workbench.html", "r") as f:
    content = f.read()

# 1. Remove the Build Databank button from the UI
content = content.replace('''<button onclick="buildDividendDatabank()" class="btn btn-secondary" style="background-color: #d9534f; color: white;"><i class="fas fa-database"></i> Build Databank</button>''', '')

# 2. Update the loadDividendsData function to handle the rebuild logic
old_load_func = '''async function loadDividendsData(forcedSymbol = null) {
    const loadBtn = document.querySelector('button[onclick="loadDividendsData()"]');
    if (loadBtn) {
        loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        loadBtn.disabled = true;
    }'''

new_load_func = '''async function loadDividendsData(forcedSymbol = null) {
    const loadBtn = document.querySelector('button[onclick="loadDividendsData()"]');
    const forceRebuildCb = document.getElementById('forceRebuildDatabank');
    if (loadBtn) {
        loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        loadBtn.disabled = true;
    }

    // First, trigger the rebuild if checked
    if (forceRebuildCb && forceRebuildCb.checked) {
        try {
            const forceStr = forceRebuildCb.checked ? 'true' : 'false';
            // Send the request and wait for it. Assuming the API returns when the celery task finishes or we just await the background trigger.
            // Wait, the API endpoint `/api/data/dividends/build-databank` triggers a Celery task and returns immediately.
            // We should ideally poll, but for now we'll wait for the task id if we modify the backend, or just wait a few seconds.
            // Let's modify the backend to return when it's done for simplicity, or we just await the fetch if the backend is updated to wait.
            // Actually, the easiest is to call the API, and since it returns immediately, wait 5 seconds.
            await fetch(`/api/data/dividends/build-databank?force=${forceStr}`, { method: 'POST' });
            // wait for a bit
            await new Promise(r => setTimeout(r, 5000));
        } catch (e) {
            console.error("Failed to build databank", e);
        }
    }'''

content = content.replace(old_load_func, new_load_func)

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(content)
