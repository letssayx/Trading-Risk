const fs = require('fs');

const path = '/app/backend/ui/static/js/opt_analysis.js';
let content = fs.readFileSync(path, 'utf8');

content = content.replace(/xAxisIndex: 1,\n\s*yAxisIndex: 2,\n\s*itemStyle: { color: '#3176B8' },/g, "xAxisIndex: 1,\n                    yAxisIndex: 2,\n                    itemStyle: { color: '#3176B8' },");

fs.writeFileSync(path, content);
console.log('Fixed opt_analysis.js');
