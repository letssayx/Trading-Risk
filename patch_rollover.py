import re

with open('backend/ui/static/js/rolloverTool.js', 'r') as f:
    content = f.read()

# Fix the keyup/input event listener to automatically restore view if empty
old_event = """            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') RolloverTool.analyzeSingle();
            });"""

new_event = """            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    if (input.value.trim() === '') {
                        RolloverTool.loadAggregatedData();
                    } else {
                        RolloverTool.analyzeSingle();
                    }
                }
            });
            input.addEventListener('input', (e) => {
                if (input.value.trim() === '') {
                    // Automatically reload the full table view when cleared
                    RolloverTool.loadAggregatedData();
                } else {
                    // Just filter the table locally while typing
                    if (document.getElementById('rollover-analysis-body')) {
                        RolloverTool.filterData();
                    }
                }
            });"""

content = content.replace(old_event, new_event)
with open('backend/ui/static/js/rolloverTool.js', 'w') as f:
    f.write(content)
