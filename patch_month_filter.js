const fs = require('fs');
let content = fs.readFileSync('backend/ui/templates/workbench.html', 'utf8');

const targetStr = `            let matchMonth = true;
            if (selectedMonths.length > 0) {
                if (!d.ex_date) {
                    matchMonth = false;
                } else {
                    const exMonth = new Date(d.ex_date).getMonth() + 1; // getMonth is 0-indexed
                    if (!selectedMonths.includes(exMonth)) matchMonth = false;
                }
            }`;

const replacementStr = `            let matchMonth = true;
            if (selectedMonths.length > 0) {
                // If there's an ex_date, filter by that.
                if (d.ex_date) {
                    const exMonth = new Date(d.ex_date).getMonth() + 1;
                    if (!selectedMonths.includes(exMonth)) matchMonth = false;
                }
                // If no ex_date (e.g. synthetic action), check broadcast_date or meeting_date
                else if (d.broadcast_date) {
                    const bMonth = new Date(d.broadcast_date).getMonth() + 1;
                    if (!selectedMonths.includes(bMonth)) matchMonth = false;
                } else {
                    // if neither exists, assume it doesn't match the month filter
                    matchMonth = false;
                }
            }`;

content = content.replace(targetStr, replacementStr);
fs.writeFileSync('backend/ui/templates/workbench.html', content);
console.log("Month Filter Patched");
