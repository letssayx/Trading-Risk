import re

for filepath in ["backend/ui/static/js/oiTool.js", "backend/ui/static/js/rolloverTool.js"]:
    with open(filepath, "r") as f:
        content = f.read()

    # The previous patch failed because the file path had an uppercase directory or something, or it wasn't the right file.
    # Actually, it didn't find the string because I searched for the string exactly, but maybe it had slightly different spacing.

    # We will use regex to replace it with the conditional block.
    content = re.sub(r'<label style="color:#ccc; font-size:12px;"><input type="checkbox" id="[^"]*-force-refresh"> Force</label>',
                     r'${window.location.pathname.includes("/workbench") ? `<label style="color:#ccc; font-size:12px;"><input type="checkbox" id="` + (filepath.includes("oiTool") ? "oi" : "rollover") + `-force-refresh"> Force</label>` : ""}',
                     content)

    with open(filepath, "w") as f:
        f.write(content)
