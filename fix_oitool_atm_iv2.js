const fs = require('fs');

const path = '/app/backend/ui/static/js/oiTool.js';
let content = fs.readFileSync(path, 'utf8');

content = content.replace(
    /<td style="padding: 8px;">\$\{\(d.atm_iv !== undefined && d.atm_iv !== null && d.atm_iv !== 0\) \? d.atm_iv.toFixed\(2\) \+ "%" : "-"\}<\/td>/g,
    '<td style="padding: 8px;">${(d.atm_iv !== undefined && d.atm_iv !== null && d.atm_iv !== 0) ? (typeof d.atm_iv === "string" ? parseFloat(d.atm_iv) : d.atm_iv).toFixed(2) + "%" : "-"}</td>'
);

content = content.replace(
    /<td style="padding: 6px 8px; color: #ccc;">\$\{\(h.atm_iv !== undefined && h.atm_iv !== null && h.atm_iv !== 0\) \? h.atm_iv.toFixed\(2\) \+ "%" : "-"\}<\/td>/g,
    '<td style="padding: 6px 8px; color: #ccc;">${(h.atm_iv !== undefined && h.atm_iv !== null && h.atm_iv !== 0) ? (typeof h.atm_iv === "string" ? parseFloat(h.atm_iv) : h.atm_iv).toFixed(2) + "%" : "-"}</td>'
);

fs.writeFileSync(path, content);
console.log('Fixed atm_iv rendering in oiTool.js');
