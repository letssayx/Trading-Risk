# If `node -c test_clean.js` passes now, it means `test_clean.js` is PERFECTLY VALID JS!
# And the only reason `script_workbench2.js` was completely broken was that it had HTML and `<script>` wrappers up to line 520, AND one backslash-escaped backtick at line 775 (originally).
# Why did it have HTML?
# Because someone did `cat workbench.html > script_workbench2.js` or a replace block merged them.
# The original valid `script_workbench2.js` must have NOT had the first 520 lines!
# I will overwrite `script_workbench2.js` with the clean JS!

import os

with open("test_clean.js", "r") as f:
    clean_js = f.read()

# I also need to make sure I don't lose the wrapper closing brace if there was one.
# Did I find `document.addEventListener('DOMContentLoaded', () => {`?
# In `test_clean.js`, is there an unbalanced bracket? `node -c` said it was valid!
# So `test_clean.js` is perfectly balanced!
with open("backend/ui/static/js/script_workbench2.js", "w") as f:
    f.write(clean_js)

print("Restored clean JS!")
