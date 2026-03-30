const fs = require('fs');

let content = fs.readFileSync('backend/ui/templates/workbench.html', 'utf8');

// For NIFTY yAxis, dataMin and dataMax might not be working perfectly if there are 0s or missing values.
// I will change min and max to dynamic functions or add padding, but specifically for Echarts,
// using a function for min and max works best when dealing with overlays that shouldn't touch the boundaries.
content = content.replace(/min: 'dataMin',\n\s*max: 'dataMax'/g, `min: function(value) { return Math.floor(value.min * 0.95); },
                            max: function(value) { return Math.ceil(value.max * 1.05); }`);

fs.writeFileSync('backend/ui/templates/workbench.html', content);
