const fs = require('fs');
let code = fs.readFileSync('backend/ui/static/js/rolloverTool.js', 'utf8');

const match = code.match(/init:[\s\S]*?\},/);
console.log("init:", match ? match[0] : "not found");
