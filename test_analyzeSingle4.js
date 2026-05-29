const fs = require('fs');
let code = fs.readFileSync('backend/ui/static/js/rolloverTool.js', 'utf8');

const match = code.match(/render:[\s\S]*?`\s*;/);
console.log("render:", match ? match[0] : "not found");
