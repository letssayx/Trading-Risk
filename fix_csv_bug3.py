# Wow. `script_workbench2.js` contains HTML at the beginning?!
# Someone literally copied `<link rel="stylesheet">` and `<style>` into `script_workbench2.js`!
# How long is this HTML chunk?
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

lines = js.split("\n")
script_tag_end = -1
for i, line in enumerate(lines[:100]):
    if "</style>" in line or "</script>" in line:
        script_tag_end = i
        print(f"End tag found at line {i}: {line.strip()}")

# Wait, `script_workbench2.js` shouldn't have ANY HTML!
