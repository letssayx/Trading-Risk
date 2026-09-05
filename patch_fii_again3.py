import re

file_path = "backend/ui/static/js/fiiTool.js"
with open(file_path, "r") as f:
    content = f.read()

# Ah! My patch for FII tool wasn't applied correctly earlier! Let's do it right.
old_start = """async function loadFiiAnalysis(event = null) {
    console.log("Loading FII Analysis Tab Data...");
    const btn = document.getElementById('btn-load-fii');
    if (btn) btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';"""

new_start = """async function loadFiiAnalysis(event = null) {
    console.log("Loading FII Analysis Tab Data...");
    const btn = document.getElementById('btn-load-fii');
    let originalText = '';
    if (btn) {
        originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        btn.disabled = true;
    }"""

content = content.replace(old_start, new_start)

old_catch = """    } catch (e) {
        console.error("Error loading FII Analysis", e);
    }
}"""

new_catch = """    } catch (e) {
        console.error("Error loading FII Analysis", e);
    } finally {
        if (btn) {
            btn.innerHTML = originalText || '<i class="fas fa-sync"></i> Refresh FII Data';
            btn.disabled = false;
        }
    }
}"""

content = content.replace(old_catch, new_catch)

with open(file_path, "w") as f:
    f.write(content)
