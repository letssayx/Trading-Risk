import re

with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
    content = f.read()

# Fix JS variables
old_js = """                            const hiOiStrikeCe = (row.highest_oi_strike_ce != null && !isNaN(Number(row.highest_oi_strike_ce))) ? Number(row.highest_oi_strike_ce).toLocaleString() : '-';
                            const pctAwayCe = (row.pct_away_highest_ce != null && !isNaN(Number(row.pct_away_highest_ce))) ? (Number(row.pct_away_highest_ce)).toFixed(2) + '%' : '-';
                            const hiOiPeValue = (row.highest_oi_pe_value != null && !isNaN(Number(row.highest_oi_pe_value))) ? Number(row.highest_oi_pe_value).toFixed(2) : '-';
                            const hiOiCeValue = (row.highest_oi_ce_value != null && !isNaN(Number(row.highest_oi_ce_value))) ? Number(row.highest_oi_ce_value).toFixed(2) : '-';"""

new_js = """                            const hiOiStrikeCe = (row.highest_oi_strike_ce != null && !isNaN(Number(row.highest_oi_strike_ce))) ? Number(row.highest_oi_strike_ce).toLocaleString() : '-';
                            const pctAwayCe = (row.pct_away_highest_ce != null && !isNaN(Number(row.pct_away_highest_ce))) ? (Number(row.pct_away_highest_ce)).toFixed(2) + '%' : '-';
                            const hiOiPeValue = (row.highest_oi_pe_value != null && !isNaN(Number(row.highest_oi_pe_value))) ? Number(row.highest_oi_pe_value).toFixed(2) : '-';
                            const hiOiCeValue = (row.highest_oi_ce_value != null && !isNaN(Number(row.highest_oi_ce_value))) ? Number(row.highest_oi_ce_value).toFixed(2) : '-';
                            const hiOiPeOi = (row.highest_oi_pe_oi != null && !isNaN(Number(row.highest_oi_pe_oi))) ? Number(row.highest_oi_pe_oi).toLocaleString() : '-';
                            const hiOiCeOi = (row.highest_oi_ce_oi != null && !isNaN(Number(row.highest_oi_ce_oi))) ? Number(row.highest_oi_ce_oi).toLocaleString() : '-';"""

content = content.replace(old_js, new_js)

# Fix JS TD
old_td = """                                <td>${hiOiStrikePe}</td>
                                <td>${pctAwayPe}</td>
                                <td>${hiOiPeValue}</td>
                                <td>${hiOiStrikeCe}</td>
                                <td>${pctAwayCe}</td>
                                <td>${hiOiCeValue}</td>"""

new_td = """                                <td>${hiOiStrikePe}</td>
                                <td>${hiOiPeOi}</td>
                                <td>${hiOiPeValue}</td>
                                <td>${pctAwayPe}</td>
                                <td>${hiOiStrikeCe}</td>
                                <td>${hiOiCeOi}</td>
                                <td>${hiOiCeValue}</td>
                                <td>${pctAwayCe}</td>"""

content = content.replace(old_td, new_td)

with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
    f.write(content)
print("Done")
