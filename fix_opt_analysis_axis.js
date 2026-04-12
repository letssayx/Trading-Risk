const fs = require('fs');

const path = '/app/backend/ui/static/js/opt_analysis.js';
let content = fs.readFileSync(path, 'utf8');

content = content.replace(`
                {
                    name: 'Put OI',
                    type: 'bar',
                    xAxisIndex: 1,
                    yAxisIndex: 2,
                    itemStyle: { color: '#3176B8' }, // Blue Puts
                    data: pe_oi
                }`, `
                {
                    name: 'Put OI',
                    type: 'bar',
                    xAxisIndex: 1,
                    yAxisIndex: 1,
                    itemStyle: { color: '#3176B8' }, // Blue Puts
                    data: pe_oi
                }`);

fs.writeFileSync(path, content);
console.log('Fixed yAxisIndex in opt_analysis.js');
