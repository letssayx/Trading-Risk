import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    html = f.read()

# Move the 4 functions (loadOptionsAnalysis, loadHighOI, loadVolatilityAnalysis, renderParticipantHistorical)
# and their related variables up into the `<script>` block that contains `loadMarketActivity`
# so they are all correctly scoped and parsed before loadMarketActivity runs!

import re

# Find the start of the block we injected previously
start_idx = html.find('let pcrChartInstance = null;')
if start_idx != -1:
    end_idx = html.find('// Listen for resize\n    window.addEventListener(\'resize\'', start_idx)
    if end_idx != -1:
        # Extract the entire block of functions we appended at the end
        functions_block = html[start_idx:end_idx]

        # Remove them from their current position at the end
        html = html[:start_idx] + html[end_idx:]

        # Now find `loadMarketActivity` and insert these functions BEFORE it in the SAME script block
        # Find `let echartInstance = null;` which is right before `loadMarketActivity`
        insert_idx = html.find('let echartInstance = null;')
        if insert_idx != -1:
            html = html[:insert_idx] + functions_block + '\n' + html[insert_idx:]

            with open('backend/ui/templates/workbench.html', 'w') as f:
                f.write(html)
            print("Successfully moved functions inside the main script block!")
        else:
            print("Could not find insert idx")
    else:
        print("Could not find end idx")
else:
    print("Could not find start idx")
