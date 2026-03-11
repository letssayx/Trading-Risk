import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Fix the generateTableHTML string literal that was cut off at line 722
cut_off_regex = r'<td style="color: \$\{parseFloat\(mwpl\) > 20 \? \'#ff4d4d\' : \'inherit\'\};\s*\n\s*async function loadTimeseriesData'

fixed_str = """<td style="color: ${parseFloat(mwpl) > 20 ? '#ff4d4d' : 'inherit'};">${mwpl}</td>
                                <td>${basis1}</td>
                                <td>${basis2}</td>
                                <td>${cal1}</td>
                                <td>${cal2}</td>
                                <td>${pe}</td>
                                <td>${b252}</td>
                                <td>${b500}</td>
                                <td>${r252}</td>
                                <td>${r500}</td>
                                <td>${pxPct}</td>
                                <td>${relVol}</td>
                                <td>${atr}</td>
                                <td>${ema20}</td>
                                <td>${ema50}</td>
                                <td>${ema100}</td>
                                <td>${ema200}</td>
                            </tr>
                        \`;
                        return html;
                }

                async function loadTimeseriesData"""

content = re.sub(cut_off_regex, fixed_str, content)

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
