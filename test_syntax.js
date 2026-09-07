const fs = require('fs');
const html = fs.readFileSync('backend/ui/templates/workbench.html', 'utf8');

// Basic script extraction and syntax check
const scripts = html.match(/<script[\s\S]*?>([\s\S]*?)<\/script>/gi);
if (scripts) {
    scripts.forEach((script, i) => {
        const content = script.replace(/<script[\s\S]*?>|<\/script>/g, '');
        try {
            new Function(content);
        } catch (e) {
            console.error(`Error in script ${i}:`, e.message);
        }
    });
}
