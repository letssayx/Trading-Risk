# If there is no `<script>` tag, then WHERE does the JS start?
# It looks like the HTML just suddenly turns into JS.
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

lines = js.split("\n")
first_js_line = -1

for i, line in enumerate(lines):
    if "function " in line or "const " in line or "let " in line or "document.addEventListener" in line:
        # Check if it's inside `<style>`
        if i > 100:
            first_js_line = i
            break

print("First possible JS line:", first_js_line)
if first_js_line != -1:
    print(lines[first_js_line-5:first_js_line+5])
