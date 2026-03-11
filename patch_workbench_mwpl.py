import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Replace mwpl logic block in generateTableHTML
old_mwpl_logic = """let mwpl = '0.00';
                            if (row.mwpl_array && Array.isArray(row.mwpl_array) && row.mwpl_array.length > 0) {
                                const firstKey = Object.keys(row.mwpl_array[0])[0];
                                mwpl = row.mwpl_array[0][firstKey].toFixed(2);
                            }"""

new_mwpl_logic = """let mwpl = '0.00';
                            let maxMwpl = 0;
                            let maxClient = '';
                            if (row.mwpl_array && Array.isArray(row.mwpl_array) && row.mwpl_array.length > 0) {
                                // mwpl_array is usually [{"client_name": value}, ...] or [value] or string.
                                // To be safe, we extract the highest value if it's an array of objects.
                                try {
                                    row.mwpl_array.forEach(item => {
                                        if (typeof item === 'object' && item !== null) {
                                            for (let key in item) {
                                                const val = parseFloat(item[key]);
                                                if (!isNaN(val) && val > maxMwpl) {
                                                    maxMwpl = val;
                                                    maxClient = key;
                                                }
                                            }
                                        } else if (typeof item === 'number') {
                                            if (item > maxMwpl) maxMwpl = item;
                                        }
                                    });
                                    if (maxMwpl > 0) {
                                        mwpl = maxMwpl.toFixed(2);
                                    } else {
                                        // fallback if structure was different
                                        const firstKey = Object.keys(row.mwpl_array[0])[0];
                                        if (firstKey) mwpl = parseFloat(row.mwpl_array[0][firstKey]).toFixed(2);
                                    }
                                } catch (e) {
                                    mwpl = '0.00';
                                }
                            }"""

if old_mwpl_logic in content:
    content = content.replace(old_mwpl_logic, new_mwpl_logic)
    with open('backend/ui/templates/workbench.html', 'w') as f:
        f.write(content)
else:
    print("Could not find MWPL logic to replace")
