const fs = require('fs');

let content = fs.readFileSync('backend/ui/static/js/opt_analysis.js', 'utf8');

content = content.replace(/min: 'dataMin',\n\s*max: 'dataMax'/g, `min: function(value) { return Math.floor(value.min * 0.95); },
                            max: function(value) { return Math.ceil(value.max * 1.05); }`);

fs.writeFileSync('backend/ui/static/js/opt_analysis.js', content);
