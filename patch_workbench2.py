import re

with open("backend/ui/templates/workbench.html", "r") as f:
    content = f.read()

# Polling logic for build databank task
new_load_func2 = '''async function loadDividendsData(forcedSymbol = null) {
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
            const buildRes = await fetch(`/api/data/dividends/build-databank?force=${forceStr}`, { method: 'POST' });
            if (buildRes.ok) {
                const buildData = await buildRes.json();
                if (buildData.task_id) {
                    // Poll celery task status
                    let isTaskDone = false;
                    while (!isTaskDone) {
                        await new Promise(r => setTimeout(r, 2000));
                        const statusRes = await fetch(`/api/v1/nse/ingest/import/status/${buildData.task_id}`);
                        if (statusRes.ok) {
                            const statusData = await statusRes.json();
                            if (statusData.status === 'SUCCESS' || statusData.status === 'FAILURE') {
                                isTaskDone = true;
                            }
                        } else {
                            // If endpoint fails, just break out and fetch data
                            isTaskDone = true;
                        }
                    }
                }
            }
        } catch (e) {
            console.error("Failed to build databank", e);
        }
    }'''

content = content.replace('''async function loadDividendsData(forcedSymbol = null) {
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
    }''', new_load_func2)

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(content)
