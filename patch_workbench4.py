with open("backend/ui/templates/workbench.html", "r") as f:
    content = f.read()

old = """                } else if (tabName === 'oi' && window.OiTool) {
                    window.OiTool.open();
                } else if (tabName === 'rollover' && window.RolloverTool) {
                    window.RolloverTool.open();
                }"""

new = """                } else if (tabName === 'oi') {
                    if (window.OiTool) window.OiTool.open();
                    else if (typeof OiTool !== 'undefined') OiTool.open();
                } else if (tabName === 'rollover') {
                    if (window.RolloverTool) window.RolloverTool.open();
                    else if (typeof RolloverTool !== 'undefined') RolloverTool.open();
                }"""

content = content.replace(old, new)

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(content)
