git restore backend/ui/templates/workbench.html
sed -i '3287,3293c\
                        }\
                    }\
                }\
            });\
\
            function addActive(items) {\
                if (!items) return false;\
                removeActive(items);\
                if (currentFocus >= items.length) currentFocus = 0;\
                if (currentFocus < 0) currentFocus = (items.length - 1);\
                items[currentFocus].classList.add("autocomplete-active");\
                items[currentFocus].scrollIntoView({ block: "nearest", behavior: "smooth" });\
            }' backend/ui/templates/workbench.html
node -e "
const fs = require('fs');
const html = fs.readFileSync('backend/ui/templates/workbench.html', 'utf8');
const scriptRegex = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
let match;
let i = 0;
while ((match = scriptRegex.exec(html)) !== null) {
  if (i === 14) {
    fs.writeFileSync('script_14_temp5.js', match[1]);
  }
  i++;
}
"
node -c script_14_temp5.js
