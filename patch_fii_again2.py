import re

file_path = "backend/ui/static/js/fiiTool.js"
with open(file_path, "r") as f:
    content = f.read()

# Make sure FII button properly sets state
old_fii = """async function loadFiiAnalysis(event = null) {
    console.log("Loading FII Analysis Tab Data...");
    const btn = document.getElementById('btn-load-fii');
    let originalText = '';
    if (btn) {
        originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        btn.disabled = true;
    }"""

new_fii = """async function loadFiiAnalysis(event = null) {
    console.log("Loading FII Analysis Tab Data...");
    const btn = document.getElementById('btn-load-fii');
    let originalText = '';
    if (btn) {
        originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        btn.disabled = true;
    }"""

content = content.replace(old_fii, new_fii)
with open(file_path, "w") as f:
    f.write(content)
