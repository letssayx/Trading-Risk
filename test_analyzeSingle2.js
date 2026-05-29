const fs = require('fs');
let code = fs.readFileSync('backend/ui/static/js/rolloverTool.js', 'utf8');

const match = code.match(/loadAggregatedData:[\s\S]*?\},/);
console.log("loadAggregatedData length:", match ? match[0].length : "not found");
console.log(match ? match[0].substring(0, 1000) : "not found");
