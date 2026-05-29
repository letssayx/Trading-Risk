import re

with open("rollover_61fb7b8.js", "r") as f:
    old_js = f.read()

# I will recreate the layout so that BOTH the original views (which render inside #rollover-results)
# AND the new single scrip details & matrix are permanently available.

# Looking at rollover_61fb7b8.js, render() did this:
"""
<div id="rollover-results" style="flex: 1; overflow: auto; padding-bottom: 20px;">
    <div style="display: flex; gap: 20px; align-items: flex-start; margin-bottom: 20px;"> ... charts etc ...</div>
    <div class="table-wrapper">
        <table class="table table-bordered table-hover">
            <thead> ... </thead>
            <tbody id="rollover-analysis-body"></tbody>
        </table>
    </div>
</div>
"""
