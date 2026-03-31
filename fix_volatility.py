# If `loadVolatilityAnalysis is not defined`, it means `script_workbench2.js` still failed to load or parse!
import subprocess

with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

with open("test_clean.js", "w") as f:
    f.write(js)

res = subprocess.run(["node", "-c", "test_clean.js"], capture_output=True, text=True)
if res.returncode == 0:
    print("Valid JS!")
else:
    print("Invalid JS:")
    print(res.stderr[:500])
