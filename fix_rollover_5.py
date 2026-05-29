import re

with open("backend/ui/static/js/rolloverTool.js", "r") as f:
    js = f.read()

# Add this.renderMatrix(this.allData, isMoM) into loadAggregatedData
update_chart_match = re.search(r'this\.updateDynamicChart\(\);', js)
if update_chart_match:
    js = js.replace("this.updateDynamicChart();", "this.updateDynamicChart();\n            this.renderMatrix(this.allData, isMoM);")
    print("Added renderMatrix to loadAggregatedData")
else:
    print("Could not find this.updateDynamicChart();")

with open("backend/ui/static/js/rolloverTool.js", "w") as f:
    f.write(js)
