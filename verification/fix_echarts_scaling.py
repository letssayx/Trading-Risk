import re

with open("backend/ui/templates/workbench.html", "r") as f:
    content = f.read()

# Let's inspect the Echarts definition again. Echarts scale config needs to be properly set.
# specifically for yAxis[1] which is the secondary Y-axis

print(content[content.find("yAxis: ["):content.find("yAxis: [")+1000])
