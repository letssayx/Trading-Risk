with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

old_block = """        window.openCronModal = async function() {
            console.log('openCronModal called');
            const modal = document.getElementById('cron-settings-modal');
            if (modal) {
                modal.style.setProperty('display', 'flex', 'important');
                modal.style.setProperty('z-index', '999999', 'important');
            } else {
                console.error('Modal element not found');
            }
            document.getElementById('cron-settings-modal').style.display = 'flex';
            try {
                await loadCronConfigs();
            } catch (e) {
                console.error("Failed to load configs", e);
                const list = document.getElementById('cron-jobs-list');
                if (list) list.innerHTML = '<div style="color: red; padding: 20px;">Failed to load configurations from server.</div>';
            }
        };"""

new_block = """        window.openCronModal = async function() {
            console.log('openCronModal called');
            const modal = document.getElementById('cron-settings-modal');
            if (modal) {
                modal.style.display = 'flex';
                modal.style.zIndex = '999999';
                modal.style.position = 'fixed';
                modal.style.top = '0';
                modal.style.left = '0';
                modal.style.width = '100vw';
                modal.style.height = '100vh';
                modal.style.backgroundColor = 'rgba(0,0,0,0.8)';
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

content = content.replace(old_block, new_block)

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
