import re

for filepath in ["backend/ui/static/js/oiTool.js", "backend/ui/static/js/rolloverTool.js"]:
    with open(filepath, "r") as f:
        content = f.read()

    if "oiTool" in filepath:
        id_str = "oi"
    else:
        id_str = "rollover"

    # Oops, my python string included literal `filepath.includes(...)` inside the JS string
    # Let's fix that.
    bad_str = r'${window.location.pathname.includes("/workbench") ? `<label style="color:#ccc; font-size:12px;"><input type="checkbox" id="` + (filepath.includes("oiTool") ? "oi" : "rollover") + `-force-refresh"> Force</label>` : ""}'
    good_str = f'${{window.location.pathname.includes("/workbench") ? `<label style="color:#ccc; font-size:12px;"><input type="checkbox" id="{id_str}-force-refresh"> Force</label>` : ""}}'

    content = content.replace(bad_str, good_str)

    with open(filepath, "w") as f:
        f.write(content)
