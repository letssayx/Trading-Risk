import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Add !important to the script for modal display to aggressively override inline CSS overrides
new_open_modal = """        window.openCronModal = async function() {
            console.log('openCronModal called');
            const modal = document.getElementById('cron-settings-modal');
            if (modal) {
                modal.style.setProperty('display', 'flex', 'important');
                modal.style.setProperty('z-index', '100000', 'important');
                modal.style.setProperty('position', 'fixed', 'important');
                modal.style.setProperty('top', '0', 'important');
                modal.style.setProperty('left', '0', 'important');
                modal.style.setProperty('width', '100vw', 'important');
                modal.style.setProperty('height', '100vh', 'important');
                modal.style.setProperty('background', 'rgba(0,0,0,0.8)', 'important');
                modal.style.setProperty('align-items', 'center', 'important');
                modal.style.setProperty('justify-content', 'center', 'important');
            } else {
                console.error('Modal element not found');
            }
            try {
                await loadCronConfigs();
            } catch (e) {
                console.error("Failed to load configs", e);
                const list = document.getElementById('cron-jobs-list');
                if (list) list.innerHTML = '<div style="color: red; padding: 20px;">Failed to load configurations from server.</div>';
            }
        };"""

content = re.sub(r'window\.openCronModal = async function\(\) \{.*?(?=        window\.closeCronModal)', new_open_modal + '\n\n', content, flags=re.DOTALL)

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
print("Updated modal patch")
