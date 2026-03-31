# The html snippet ends exactly at `// script start` at line 520!
# It's as if someone copied `workbench.html` partially and pasted it.
# Let's see if the rest of `script_workbench2.js` is pure JS.
# If I delete lines 1 to 520, will `script_workbench2.js` be valid JS?
import subprocess

with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

lines = js.split("\n")
clean_js = "\n".join(lines[521:])
with open("test_clean.js", "w") as f:
    f.write(clean_js)

res = subprocess.run(["node", "-c", "test_clean.js"], capture_output=True, text=True)
if res.returncode == 0:
    print("Valid JS after removing first 520 lines!")
else:
    print("Invalid JS after removing first 520 lines:")
    print(res.stderr[:500])
