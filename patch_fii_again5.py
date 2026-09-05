import re

file_path = "backend/ui/templates/workbench.html"
with open(file_path, "r") as f:
    content = f.read()

old_catch = """        } catch(e) {
            console.error(e);
            tbody.innerHTML = '<tr><td colspan="15" style="text-align:center; color:#f44336;">Error loading Market Watch data</td></tr>';
        } finally {
            if (loadBtn && isRefresh) {
                loadBtn.innerHTML = originalText;
                loadBtn.disabled = false;
            }
        }
    }"""

# A bug in my previous patch: if `isRefresh` is false, `originalText` is empty, so if it goes to `finally` block and isRefresh is false it doesn't run the `if`. That's correct.
# But let's check `loadMarketWatch()` when it's called with NO arguments: loadBtn is still found. isRefresh is false. loadBtn.innerHTML is NOT updated. It won't reset. That's fine.
# But wait, what if `loadBtn` doesn't match the selector?
# `<button class="btn btn-primary" onclick="loadMarketWatch(true)"><i class="fas fa-sync"></i> Refresh Basis</button>`
# This selector `button[onclick="loadMarketWatch(true)"]` matches it perfectly.

# Let's ensure originalText has a fallback just in case.
new_catch = """        } catch(e) {
            console.error(e);
            tbody.innerHTML = '<tr><td colspan="15" style="text-align:center; color:#f44336;">Error loading Market Watch data</td></tr>';
        } finally {
            if (loadBtn && isRefresh) {
                loadBtn.innerHTML = originalText || '<i class="fas fa-sync"></i> Refresh Basis';
                loadBtn.disabled = false;
            }
        }
    }"""

content = content.replace(old_catch, new_catch)

with open(file_path, "w") as f:
    f.write(content)
