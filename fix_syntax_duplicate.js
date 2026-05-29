const fs = require('fs');
let js = fs.readFileSync('backend/ui/static/js/rolloverTool.js', 'utf8');

// I replaced it twice with my scripts. Let's fix it by pulling from 61fb7b8, applying only the necessary patches cleanly.
