const fs = require('fs');
let content = fs.readFileSync('backend/ui/templates/workbench.html', 'utf8');

const targetStr = "let filteredActions = divRawData.filter(d => {";

const replacementStr = `
        // Create synthetic actions from board meetings that don't have a corporate action yet
        let combinedActions = [...divRawData];

        // Find board meetings discussing dividends that don't have a linked corporate action
        Object.keys(meetingsBySymbol).forEach(sym => {
            const meetings = meetingsBySymbol[sym];
            meetings.forEach(m => {
                const purpose = (m.purpose || '').toLowerCase();
                if (purpose.includes('dividend') || purpose.includes('bonus') || purpose.includes('split') || purpose.includes('sub-division')) {
                    // Check if there is a corporate action after this meeting date
                    const mDate = m.meeting_date ? new Date(m.meeting_date) : null;
                    let hasLinkedAction = false;

                    if (mDate) {
                        for (let a of divRawData) {
                            if (a.symbol === sym) {
                                const aDate = a.ex_date ? new Date(a.ex_date) : null;
                                // If the corporate action ex_date is after the meeting date, consider it linked
                                if (aDate && aDate >= mDate) {
                                    hasLinkedAction = true;
                                    break;
                                }
                            }
                        }
                    }

                    if (!hasLinkedAction) {
                        // Create a synthetic action

                        // Parse dividend amount if available (e.g., "Rs. 54 per share" or "54/-")
                        let amount = null;
                        let divType = '-';
                        if (purpose.includes('dividend')) {
                             divType = 'Dividend';
                             if (purpose.includes('interim')) divType = 'Interim';
                             if (purpose.includes('special')) divType = 'Special';
                             if (purpose.includes('final')) divType = 'Final';

                             // Try to extract amount
                             let amountMatch = purpose.match(/(?:rs\\.?|rupees?)\\s*([0-9]+(?:\\.[0-9]+)?)/i) || purpose.match(/([0-9]+(?:\\.[0-9]+)?)\\s*\\/\\-/i) || purpose.match(/dividend\\s+of\\s+([0-9]+(?:\\.[0-9]+)?)/i);
                             if (amountMatch) {
                                 amount = amountMatch[1];
                             }
                        } else if (purpose.includes('bonus')) {
                             divType = 'Bonus';
                        } else if (purpose.includes('split') || purpose.includes('sub-division')) {
                             divType = 'Split';
                        }

                        combinedActions.push({
                            symbol: sym,
                            company_name: m.company_name || sym,
                            purpose: m.purpose,
                            subject: m.purpose, // use purpose as subject
                            dividend_type: divType,
                            ex_date: null,
                            record_date: null,
                            broadcast_date: m.broadcast_date || m.date,
                            parsed_dividend_amount: amount,
                            is_synthetic: true, // flag to identify
                            _matchedMeeting: m // store the meeting to avoid re-matching
                        });
                    }
                }
            });
        });

        let filteredActions = combinedActions.filter(d => {`;

content = content.replace(targetStr, replacementStr);
fs.writeFileSync('backend/ui/templates/workbench.html', content);
console.log("Patched");
