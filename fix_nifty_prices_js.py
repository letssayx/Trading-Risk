with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js_code = f.read()

# Make sure we ignore 0s and nulls when finding min/max so we don't scale to zero
js_code = js_code.replace("const validNifty = niftyData.filter(v => v !== null && !isNaN(v));",
"const validNifty = niftyData.filter(v => v !== null && !isNaN(v) && v > 0);")

with open("backend/ui/static/js/script_workbench2.js", "w") as f:
    f.write(js_code)

print("JS patched")
