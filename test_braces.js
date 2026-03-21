const fs = require('fs');
const html = fs.readFileSync('script_14_temp.js', 'utf8');
let script = html;
let openBraces = (script.match(/\{/g) || []).length;
let closeBraces = (script.match(/\}/g) || []).length;
console.log(`Open: ${openBraces}, Close: ${closeBraces}`);
