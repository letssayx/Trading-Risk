with open('./backend/ui/static/js/rolloverTool.js', 'r') as f:
    content = f.read()

content = content.replace("    }\n\n    exportMatrixCSV: function() {", "    },\n\n    exportMatrixCSV: function() {")

with open('./backend/ui/static/js/rolloverTool.js', 'w') as f:
    f.write(content)
