const fs = require('fs');
let js = fs.readFileSync("backend/ui/static/js/rolloverTool.js", "utf8");

// Fix syntax error - add missing comma before exportMatrixCSV if needed.
js = js.replace("    }\n\n    exportMatrixCSV", "    },\n\n    exportMatrixCSV");

fs.writeFileSync("backend/ui/static/js/rolloverTool.js", js);
