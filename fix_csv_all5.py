import re

with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

# It looks like I matched `deriv-tab-matrix` but didn't successfully append the button because `class="deriv-sub-tab active"` had `active` in it!
# For basis and chain, their IDs are probably different!
# Let's search for `Basis Watch` and `Option Chain` and `Data Matrix` headings or tabs in the HTML!

print("Basis Watch matches:", re.findall(r'<div[^>]*id="[^"]*basis[^"]*"[^>]*>', html))
print("Option Chain matches:", re.findall(r'<div[^>]*id="[^"]*chain[^"]*"[^>]*>', html))
