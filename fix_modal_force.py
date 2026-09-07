with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Make the modal directly visible via hardcoded style block instead of inline JS
# Sometimes JS frameworks or other styles block inline styles.
block_to_replace = """    <!-- Cron Settings Modal -->
    <div id="cron-settings-modal" class="modal-overlay" style="display:none; z-index:10000; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); align-items:center; justify-content:center;">"""

new_block = """    <!-- Cron Settings Modal -->
    <div id="cron-settings-modal" class="modal-overlay" style="display:none; z-index:100000; position:fixed !important; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.8); align-items:center; justify-content:center;">"""

content = content.replace(block_to_replace, new_block)

js_to_replace = """        window.openCronModal = async function() {
            console.log('openCronModal called');
            const modal = document.getElementById('cron-settings-modal');
            if (modal) {
                modal.style.setProperty('display', 'flex', 'important');
                modal.style.zIndex = '10000';
                modal.style.position = 'fixed';
                modal.style.top = '0';
                modal.style.left = '0';
                modal.style.width = '100%';
                modal.style.height = '100%';
                modal.style.background = 'rgba(0,0,0,0.7)';
                modal.style.alignItems = 'center';
                modal.style.justifyContent = 'center';
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

new_js = """        window.openCronModal = async function() {
            console.log('openCronModal called');
            const modal = document.getElementById('cron-settings-modal');
            if (modal) {
                modal.style.cssText = 'display: flex !important; z-index: 100000 !important; position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; background: rgba(0,0,0,0.8) !important; align-items: center !important; justify-content: center !important;';
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

content = content.replace(js_to_replace, new_js)

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
