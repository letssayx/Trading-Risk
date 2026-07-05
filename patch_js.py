import re

with open('backend/ui/static/js/uploadModal.js', 'r') as f:
    content = f.read()

# Make buttons look for running task or use force-kill-all
patch_js = """
// Expose the active task id check directly from fetch status
let _currentRunningTaskId = null;
"""

if "_currentRunningTaskId" not in content:
    content = "_currentRunningTaskId = null;\n" + content

    # Let's replace the button logic
    # Find existing pause btn
    pause_rgx = re.compile(r'pauseBtn\.addEventListener\(\'click\',\s*async\s*\(\)\s*=>\s*\{.*?(?=\s+resumeBtn)', re.DOTALL)

    resume_rgx = re.compile(r'resumeBtn\.addEventListener\(\'click\',\s*async\s*\(\)\s*=>\s*\{.*?(?=\s+killBtn)', re.DOTALL)

    kill_rgx = re.compile(r'killBtn\.addEventListener\(\'click\',\s*async\s*\(\)\s*=>\s*\{.*?(?=\s*\}\);)', re.DOTALL)

    content = re.sub(pause_rgx, """pauseBtn.addEventListener('click', async () => {
        let taskId = localStorage.getItem('activeImportTaskId') || _currentRunningTaskId;
        if (!taskId) {
            const statusUrl = new URL('/api/v1/nse/ingest/import/status/last', window.location.origin);
            // This assumes we have a way to get the last task if we implement it, but for now we fallback
            alert("No active task tracked by UI. Try reloading the page if a task is running.");
            return;
        }

        try {
            const resp = await fetch(`/api/v1/nse/ingest/import/pause/${taskId}`, { method: 'POST' });
            const data = await resp.json();
            alert(data.message || "Task paused.");
        } catch (e) {
            console.error(e);
            alert("Failed to pause task.");
        }
    });""", content)

    content = re.sub(resume_rgx, """resumeBtn.addEventListener('click', async () => {
        let taskId = localStorage.getItem('activeImportTaskId') || _currentRunningTaskId;
        if (!taskId) {
            alert("No active task tracked by UI.");
            return;
        }

        try {
            const resp = await fetch(`/api/v1/nse/ingest/import/resume/${taskId}`, { method: 'POST' });
            const data = await resp.json();
            alert(data.message || "Task resumed.");
        } catch (e) {
            console.error(e);
            alert("Failed to resume task.");
        }
    });""", content)

    content = re.sub(kill_rgx, """killBtn.addEventListener('click', async () => {
        let taskId = localStorage.getItem('activeImportTaskId') || _currentRunningTaskId;
        try {
            if (taskId) {
                const resp = await fetch(`/api/v1/nse/ingest/import/force-kill/${taskId}`, { method: 'POST' });
                const data = await resp.json();
                alert(data.message || "Task forcefully terminated.");
                localStorage.removeItem('activeImportTaskId');
                _currentRunningTaskId = null;
            } else {
                // If no specific task id is found, use the catch-all
                const resp = await fetch(`/api/v1/nse/ingest/import/force-kill-all`, { method: 'POST' });
                const data = await resp.json();
                alert(data.message || "All import tasks forcefully terminated.");
            }
            if (window.pollingInterval) clearInterval(window.pollingInterval);
        } catch (e) {
            console.error(e);
            alert("Failed to kill task.");
        }
    });""", content)

    with open('backend/ui/static/js/uploadModal.js', 'w') as f:
        f.write(content)
