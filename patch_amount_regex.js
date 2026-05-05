const fs = require('fs');
let content = fs.readFileSync('backend/ui/templates/workbench.html', 'utf8');

const targetStr = `let amountMatch = purpose.match(/(?:rs\\\\.?|rupees?)\\\\s*([0-9]+(?:\\\\.[0-9]+)?)/i) || purpose.match(/([0-9]+(?:\\\\.[0-9]+)?)\\\\s*\\\\/\\\\-/i) || purpose.match(/dividend\\\\s+of\\\\s+([0-9]+(?:\\\\.[0-9]+)?)/i);`;

const replacementStr = `let amountMatch = purpose.match(/(?:rs\\\\.?|rupees?)\\\\s*([0-9]+(?:\\\\.[0-9]+)?)/i) || purpose.match(/([0-9]+(?:\\\\.[0-9]+)?)\\\\s*\\\\/\\\\-/i) || purpose.match(/dividend\\\\s+of\\\\s+([0-9]+(?:\\\\.[0-9]+)?)/i) || purpose.match(/dividend.*?\\\\s+([0-9]+(?:\\\\.[0-9]+)?)\\\\s+per/i);`;

content = content.replace(targetStr, replacementStr);
fs.writeFileSync('backend/ui/templates/workbench.html', content);
console.log("Regex Patched");
