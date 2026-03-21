const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('backend/ui/templates/workbench.html', 'utf8');
const scriptRegex = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
let match;
let i = 0;
while ((match = scriptRegex.exec(html)) !== null) {
  if (match[1].trim()) {
    try {
      new vm.Script(match[1]);
      console.log(`Script ${i} OK`);
    } catch (e) {
      console.error(`Script ${i} ERROR:`, e.message);
    }
  }
  i++;
}
