import re

file_path = "backend/ui/static/js/opt_analysis.js"
with open(file_path, "r") as f:
    content = f.read()

# Oh, the sorting is a - b already:
# .sort((a, b) => a.strike - b.strike);
# But for a butterfly chart where the Y axis is on the left or middle and is vertical, Echarts plots the first data point at the bottom and goes UP.
# So if the data is sorted ascending (low to high), the lowest strike is at the bottom, highest strike is at the top.
# The user wants "High OI Butterfly chart strikes are sorted backwards (high-to-low)." Wait, the user said "strikes are sorted backwards".
# Actually, if it goes from lowest at the bottom to highest at the top, that usually feels correct for a y-axis (price goes up).
# But for an option chain butterfly chart, we often want the lower strikes at the top and higher strikes at the bottom (like the actual NSE option chain).
# Let's reverse the sort to b.strike - a.strike.

search = "sort((a, b) => a.strike - b.strike);"
replace = "sort((a, b) => b.strike - a.strike);"

content = content.replace(search, replace)

with open(file_path, "w") as f:
    f.write(content)
