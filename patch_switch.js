const fs = require('fs');
let content = fs.readFileSync('backend/ui/templates/workbench.html', 'utf8');

// The original switchMainTab is defined in the script block in workbench.html usually
// Let's check if it exists there
