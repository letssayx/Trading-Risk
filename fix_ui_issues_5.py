import re

def fix_ui_issues_5():
    with open('backend/ui/templates/workbench.html', 'r') as f:
        html = f.read()

    # Make lower-left table overflow properly in split view by setting exact width and flex basis
    html = html.replace('<div id="oi-tool-container" style="flex: 1; display: flex; flex-direction: column; min-width: 0;">', '<div id="oi-tool-container" style="flex: 1 1 50%; max-width: 50%; display: flex; flex-direction: column; min-width: 0; overflow-x: auto;">')
    html = html.replace('<div style="flex: 1; display: flex; flex-direction: column; gap: 20px; min-width: 0;">', '<div style="flex: 1 1 50%; max-width: 50%; display: flex; flex-direction: column; gap: 20px; min-width: 0;">')

    with open('backend/ui/templates/workbench.html', 'w') as f:
        f.write(html)

if __name__ == '__main__':
    fix_ui_issues_5()
