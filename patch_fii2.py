import re

# 1. Fix FII button to be blue
file_path = "backend/ui/templates/derivatives.html"
with open(file_path, "r") as f:
    content = f.read()

content = content.replace('<button class="btn btn-secondary" id="btn-load-fii"', '<button class="btn btn-primary" id="btn-load-fii"')

with open(file_path, "w") as f:
    f.write(content)

# 2. Fix the `loadMarketWatch` spinner logic in workbench.html
# My previous patch might have been overwritten or not correctly matched.
file_path = "backend/ui/templates/workbench.html"
with open(file_path, "r") as f:
    content = f.read()

# I will replace the start of loadMarketWatch manually
old_start = """    async function loadMarketWatch(isRefresh = false) {
        const tbody = document.getElementById('marketwatch-body');
        // The user explicitly requested to remove the date input requirement for marketwatch.
        // It will automatically pull the latest F&O data.
        tbody.innerHTML = '<tr><td colspan="15" style="text-align:center; color:#888;">Loading...</td></tr>';"""

new_start = """    async function loadMarketWatch(isRefresh = false) {
        const tbody = document.getElementById('marketwatch-body');
        const loadBtn = document.querySelector('button[onclick="loadMarketWatch(true)"]');
        let originalText = '';
        if (loadBtn && isRefresh) {
            originalText = loadBtn.innerHTML;
            loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            loadBtn.disabled = true;
        }

        // The user explicitly requested to remove the date input requirement for marketwatch.
        // It will automatically pull the latest F&O data.
        tbody.innerHTML = '<tr><td colspan="15" style="text-align:center; color:#888;">Loading...</td></tr>';"""

content = content.replace(old_start, new_start)

old_catch = """        } catch(e) {
            console.error(e);
            tbody.innerHTML = '<tr><td colspan="15" style="text-align:center; color:#f44336;">Error loading Market Watch data</td></tr>';
        }
    }"""

new_catch = """        } catch(e) {
            console.error(e);
            tbody.innerHTML = '<tr><td colspan="15" style="text-align:center; color:#f44336;">Error loading Market Watch data</td></tr>';
        } finally {
            if (loadBtn && isRefresh) {
                loadBtn.innerHTML = originalText;
                loadBtn.disabled = false;
            }
        }
    }"""

content = content.replace(old_catch, new_catch)

with open(file_path, "w") as f:
    f.write(content)
