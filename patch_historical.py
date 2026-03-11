import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# 1. Historical Data Tab Dropdown
hist_dropdown_search = '<option value="fii_stats">FII Derivatives Stats</option>'
hist_dropdown_replace = '<option value="fii_stats">FII Derivatives Stats</option>\n                                    <option value="fii_dii_cash">FII/DII Cash Flow</option>'
if hist_dropdown_search in content:
    content = content.replace(hist_dropdown_search, hist_dropdown_replace)
else:
    print("Could not find historical dropdown")

# 2. Import Data Tab - Latest
latest_search = '<label class="checkbox-label"><input type="checkbox" class="latest-type" value="fii_derivatives_stats"> FII Stats</label>'
latest_replace = '<label class="checkbox-label"><input type="checkbox" class="latest-type" value="fii_derivatives_stats"> FII Stats</label>\n                                <label class="checkbox-label"><input type="checkbox" class="latest-type" value="fii_dii_cash"> FII/DII Cash</label>'
if latest_search in content:
    content = content.replace(latest_search, latest_replace)
else:
    print("Could not find latest import")

# 3. Import Data Tab - Historical Range
range_search = '<label class="checkbox-label"><input type="checkbox" class="range-type" value="fii_derivatives_stats"> FII Stats</label>'
range_replace = '<label class="checkbox-label"><input type="checkbox" class="range-type" value="fii_derivatives_stats"> FII Stats</label>\n                                <label class="checkbox-label"><input type="checkbox" class="range-type" value="fii_dii_cash"> FII/DII Cash</label>'
if range_search in content:
    content = content.replace(range_search, range_replace)
else:
    print("Could not find range import")

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
