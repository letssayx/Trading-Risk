git restore backend/ui/templates/workbench.html
sed -i '3287,3293c\
                        }\
                    }\
                }\
            });' backend/ui/templates/workbench.html
node -e "
const fs = require('fs');
const html = fs.readFileSync('backend/ui/templates/workbench.html', 'utf8');
const scriptRegex = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
let match;
let i = 0;
while ((match = scriptRegex.exec(html)) !== null) {
  if (i === 14) {
    fs.writeFileSync('script_14_temp4.js', match[1]);
  }
  i++;
}
"
node -c script_14_temp4.js
