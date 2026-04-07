filepath = "backend/ui/static/js/oiTool.js"
with open(filepath, "r") as f:
    content = f.read()

# Let's wrap the content of `loadAggregatedData` and `renderAggregatedView` in a broad try/catch to log the exact error to the console.

content = content.replace(
"""            this.allData = data.data || [];
            this.filterData();""",
"""            this.allData = data.data || [];
            try {
                this.filterData();
            } catch (e) {
                console.error("CRASH in filterData:", e);
                alert("Render crash! Check console: " + e.message);
            }"""
)

with open(filepath, "w") as f:
    f.write(content)
print("Added JS debug bounds")
