import re
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

# Let's search backwards from `switchDerivTab` to find the actual start of JS script tag
idx_end_script = js.find('</script>', 0, js.find('switchDerivTab'))
if idx_end_script == -1:
    idx_script = js.find('<script>', 0, js.find('switchDerivTab'))
    if idx_script != -1:
        print("Found <script> at", idx_script)
        # We need to strip everything up to and including `<script>`
        new_js = js[idx_script+8:]
        with open("backend/ui/static/js/script_workbench2.js", "w") as f:
            f.write(new_js)
        print("Fixed script_workbench2.js by removing HTML.")
    else:
        print("Could not find <script> tag before JS logic.")
else:
    print("Found </script> before JS logic! Something is very wrong.")
