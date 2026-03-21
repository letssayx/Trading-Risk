import re

file_path = 'backend/ui/templates/workbench.html'
with open(file_path, 'r') as f:
    content = f.read()

# Replace the colspan in 'No data found'
content = content.replace('<td colspan="10" style="text-align:center', '<td colspan="7" style="text-align:center')

# Now let's find the loop where rows are generated
old_loop_pattern = r'filteredActions\.forEach\(d => \{.*?tbodyActions\.appendChild\(tr\);\n        \}\);'

new_loop = """filteredActions.forEach(d => {
            const tr = document.createElement('tr');

            // Symbol/Series mapping
            let series = d.symbol || '-';

            // Find matching board meeting based on closest date prior to ex_date
            let matchingMeetings = meetingsBySymbol[series.toUpperCase()] || [];
            let bmd = '-';
            let agm = '-';

            if (matchingMeetings.length > 0) {
                // If we have an ex-date, try to find a meeting date before or exactly matching it
                let exDateObj = d.ex_date ? new Date(d.ex_date) : null;

                // Sort meetings by meeting date desc
                matchingMeetings.sort((a,b) => new Date(b.meeting_date || 0) - new Date(a.meeting_date || 0));

                for (let m of matchingMeetings) {
                    if (!exDateObj || new Date(m.meeting_date) <= exDateObj) {
                        bmd = m.meeting_date || '-';
                        if (m.purpose && m.purpose.toUpperCase().includes('AGM')) {
                            agm = m.meeting_date || '-';
                        }
                        break;
                    }
                }

                // If still not found and we have some meetings, just take the most recent one for the symbol
                if (bmd === '-') {
                    bmd = matchingMeetings[0].meeting_date || '-';
                    if (matchingMeetings[0].purpose && matchingMeetings[0].purpose.toUpperCase().includes('AGM')) {
                        agm = matchingMeetings[0].meeting_date || '-';
                    }
                }
            }

            // "SERIES", "FACE VALUE", "PURPOSE", "EX-DATE", "RECORD DATE", "BOARD MEETING DATE", "AGM/EGM DATE"
            // We'll extract purpose string from d.subject or d.purpose
            let fullPurpose = d.subject || d.purpose || '-';

            // Calculate a formatted face value (if present)
            let faceValue = d.face_value || '-';
            if (faceValue === '-' && fullPurpose.toUpperCase().includes('FACE VALUE')) {
                 let match = fullPurpose.match(/FACE VALUE[:\s]+([\d\.]+)/i);
                 if (match) faceValue = match[1];
            }

            tr.innerHTML = `
                <td>${series}</td>
                <td>${faceValue}</td>
                <td>${fullPurpose}</td>
                <td>${d.ex_date || '-'}</td>
                <td>${d.record_date || '-'}</td>
                <td>${bmd}</td>
                <td>${agm}</td>
            `;
            tbodyActions.appendChild(tr);
        });"""

content = re.sub(old_loop_pattern, new_loop, content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(content)

print("Updated rendering logic for Dividends tab.")
