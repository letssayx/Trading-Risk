import re

def fix_ui_issues_4():
    with open('backend/ui/static/css/styles.css', 'r') as f:
        css = f.read()

    # Make lower-left table overflow properly in split view
    if ".table-wrapper {" in css:
        pass # Probably already has overflow

    # We should make sure oi-tool-container doesn't squash the table
    # We can do this in the workbench.html file

    with open('backend/ui/templates/workbench.html', 'r') as f:
        html = f.read()

    # Let's adjust flex sizing to avoid squashing. Both containers flex: 1 by default, but maybe minimum height is needed.
    # In 'deriv-tab-oi', we have <div id="oi-tool-container" style="flex: 1; display: flex; flex-direction: column; min-width: 0;">
    # In oiTool.js, the table is: <div class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow-x: auto; flex: 1; min-height: 300px;">
    # It might need 'flex: 1 1 50%' instead.

    html = html.replace('<div id="oi-tool-container" style="flex: 1; display: flex; flex-direction: column; min-width: 0;">', '<div id="oi-tool-container" style="flex: 1; display: flex; flex-direction: column; min-width: 0; flex-basis: 50%; max-width: 50%; overflow-x: auto;">')
    html = html.replace('<div style="flex: 1; display: flex; flex-direction: column; gap: 20px; min-width: 0;">', '<div style="flex: 1; display: flex; flex-direction: column; gap: 20px; min-width: 0; flex-basis: 50%; max-width: 50%;">')

    with open('backend/ui/templates/workbench.html', 'w') as f:
        f.write(html)

if __name__ == '__main__':
    fix_ui_issues_4()
