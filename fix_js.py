with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
    content = f.read()

# Make sure uploader opening doesn't lead to infinite loops if we switch to 'import' but there is no 'import' panel,
# or we just need to return immediately after opening the uploader so it doesn't break.
content = content.replace("if (tabName === 'import' && window.uploader) window.uploader.open();",
                          "if (tabName === 'import' && window.uploader) { window.uploader.open(); return; }")

with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
    f.write(content)
