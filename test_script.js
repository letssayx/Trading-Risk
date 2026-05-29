const fs = require('fs');
let code = fs.readFileSync('backend/ui/static/js/rolloverTool.js', 'utf8');

// Looking closely at analyzeSingle
const match = code.match(/analyzeSingle:\s*async\s*function\s*\(\)\s*\{([\s\S]*?)handleTick:/);
if (match) {
    console.log(match[1].substring(0, 500));
} else {
    console.log("Could not find analyzeSingle");
}
