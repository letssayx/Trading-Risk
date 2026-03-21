import re

file_path = 'backend/ui/templates/workbench.html'
with open(file_path, 'r') as f:
    content = f.read()

# Replace the colspan in 'No data found'
content = content.replace('<td colspan="10" style="text-align:center', '<td colspan="7" style="text-align:center')

# Now let's find the loop where rows are generated
old_loop_pattern = r'filteredActions\.forEach\(d => \{.*?tbodyActions\.appendChild\(tr\);\n        \}\);'

def replacer(match):
    return """filteredActions.forEach(d => {
            const tr = document.createElement('tr');

            let series = d.symbol || '-';

            let matchingMeetings = meetingsBySymbol[series.toUpperCase()] || [];
            let bmd = '-';
            let agm = '-';

            if (matchingMeetings.length > 0) {
                let exDateObj = d.ex_date ? new Date(d.ex_date) : null;

                matchingMeetings.sort((a,b) => {
                    let dateA = a.meeting_date ? new Date(a.meeting_date) : new Date(0);
                    let dateB = b.meeting_date ? new Date(b.meeting_date) : new Date(0);
                    return dateB - dateA;
                });

                for (let m of matchingMeetings) {
                    if (!exDateObj || (m.meeting_date && new Date(m.meeting_date) <= exDateObj)) {
                        bmd = m.meeting_date || '-';
                        if (m.purpose && m.purpose.toUpperCase().includes('AGM')) {
                            agm = m.meeting_date || '-';
                        }
                        break;
                    }
                }

                if (bmd === '-') {
                    bmd = matchingMeetings[0].meeting_date || '-';
                    if (matchingMeetings[0].purpose && matchingMeetings[0].purpose.toUpperCase().includes('AGM')) {
                        agm = matchingMeetings[0].meeting_date || '-';
                    }
                }
            }

            let fullPurpose = d.subject || d.purpose || '-';

            let faceValue = d.face_value || d.faceValue || '-';
            if (faceValue === '-' && fullPurpose.toUpperCase().includes('FACE VALUE')) {
                 let match = fullPurpose.match(/FACE VALUE[:\\s]+([\\d\\.]+)/i);
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

content = re.sub(old_loop_pattern, replacer, content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(content)

print("Updated rendering logic for Dividends tab.")
