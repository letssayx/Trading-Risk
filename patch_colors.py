import re

files = [
    "backend/ui/templates/derivatives.html",
    "backend/ui/templates/workbench.html",
    "backend/ui/static/js/mwplTool.js",
    "backend/ui/static/js/script_workbench2.js",
    "backend/ui/static/js/fiiTool.js"
]

def replace_in_file(filepath, search, replace):
    with open(filepath, "r") as f:
        content = f.read()
    content = content.replace(search, replace)
    with open(filepath, "w") as f:
        f.write(content)

# 1. Change MWPL Refresh Button
replace_in_file(
    "backend/ui/templates/derivatives.html",
    '<button class="btn btn-secondary" id="btn-load-mwpl" onclick="loadMWPLAnalysis(true)"><i class="fas fa-sync"></i> Refresh MWPL</button>',
    '<button class="btn btn-primary" id="btn-load-mwpl" onclick="loadMWPLAnalysis(true)"><i class="fas fa-sync"></i> Refresh MWPL</button>'
)
replace_in_file(
    "backend/ui/templates/workbench.html",
    '<button class="btn btn-secondary" id="btn-load-mwpl" onclick="loadMWPLAnalysis(true)"><i class="fas fa-sync"></i> Refresh MWPL</button>',
    '<button class="btn btn-primary" id="btn-load-mwpl" onclick="loadMWPLAnalysis(true)"><i class="fas fa-sync"></i> Refresh MWPL</button>'
)

# 2. Change Basis Refresh Button
replace_in_file(
    "backend/ui/templates/workbench.html",
    '<button class="btn btn-secondary" onclick="loadMarketWatch(true)"><i class="fas fa-sync"></i> Refresh Basis</button>',
    '<button class="btn btn-primary" onclick="loadMarketWatch(true)"><i class="fas fa-sync"></i> Refresh Basis</button>'
)

# 3. Fix mwplTool.js spinner logic
# It needs to revert button state.
mwpl_js = ""
with open("backend/ui/static/js/mwplTool.js", "r") as f:
    mwpl_js = f.read()

# Add finally block to revert loadBtn
old_catch = """        } catch (e) {
            console.error("Failed to load MWPL Analysis", e);
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#f48771;">Error loading data: ${e.message}</td></tr>`;
        }
    }"""
new_catch = """        } catch (e) {
            console.error("Failed to load MWPL Analysis", e);
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#f48771;">Error loading data: ${e.message}</td></tr>`;
        } finally {
            if (loadBtn) {
                loadBtn.innerHTML = originalText;
                loadBtn.disabled = false;
            }
        }
    }"""
if old_catch in mwpl_js:
    mwpl_js = mwpl_js.replace(old_catch, new_catch)
    # Remove the existing cleanup logic if any
    mwpl_js = mwpl_js.replace("        if (loadBtn) {\n            loadBtn.disabled = false;\n            loadBtn.innerHTML = originalText;\n        }", "")

with open("backend/ui/static/js/mwplTool.js", "w") as f:
    f.write(mwpl_js)
