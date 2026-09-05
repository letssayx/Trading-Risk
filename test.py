with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    text = f.read()

print("DOMContentLoaded" in text)
print("marketWatchDataCache" in text)
