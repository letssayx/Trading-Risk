const fs = require('fs');
let code = fs.readFileSync('backend/ui/static/js/rolloverTool.js', 'utf8');

// Looking closely at filterData and handleTick, and also where data gets loaded.
const match = code.match(/filterData:[\s\S]*?\},/);
console.log("filterData:", match ? match[0] : "not found");

const match2 = code.match(/syncAndLoadAggregatedData:[\s\S]*?\},/);
console.log("syncAndLoad:", match2 ? match2[0] : "not found");
