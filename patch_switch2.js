const fs = require('fs');
let content = fs.readFileSync('backend/ui/static/js/script_workbench2.js', 'utf8');

const regex = /if \(tabName === 'ai_analyze'\) fetchSystemAccuracy\(\);/;
content = content.replace(regex, "if (tabName === 'ai_analyze') fetchSystemAccuracy();\n            if (tabName === 'skill_studio' && window.loadSkillList) window.loadSkillList();");

fs.writeFileSync('backend/ui/static/js/script_workbench2.js', content, 'utf8');
