with open("backend/ui/static/js/mutualFund.js", "r") as f:
    content = f.read()

if "loadMfFilters(); // Temporarily disabled" in content:
    print("MF Patch successful!")
else:
    print("MF Patch failed.")
