# The CSV logic seems solid.
# Wait! `csvRows.push(headers.join(','));`
# The headers array is built earlier:
# `let headers = ['Date'];`
# `seriesNames.forEach(name => { headers.push(`"${name}"`); });`
# Then: `csvRows.push(headers.join(','));`
# The rows loop:
# `for (let i = 0; i < len; i++) { ... }`
# `csvRows.push(row.join(','));`
# `const csvFile = new Blob([csvRows.join('\n')], { type: 'text/csv' });`

# Wait, `isChartJS = typeof chartInstance.config !== 'undefined';`
# `isECharts = typeof chartInstance.getOption === 'function';`
# What if it's an HTML Table??
# The user said "not a single existing CSV that you provided download anything".
# "CSV needed in each chart AND TABLE in each tab".
# I provided `exportTableToCSV` but maybe they are calling `exportChartDataToCSV` on a table?
# Or maybe the button `onclick` handlers are throwing reference errors because the charts/tables are dynamically created and the variables are null when the page loads?
# Yes! `if(window.volPreExpiryChart) exportChartDataToCSV(window.volPreExpiryChart, 'Vol_Pre_Expiry')`
# Wait, if `window.volPreExpiryChart` is false, it does `else exportChartDataToCSV(volPreExpiryChart, 'Vol_Pre_Expiry')`.
# If `volPreExpiryChart` is `null`, `exportChartDataToCSV` alerts "Chart is not loaded or data is empty."
# BUT THE USER SAID NO ERROR, NO ALERT.

# Let's inspect ONE specific CSV button. "Volatility Analysis CSV".
# In `workbench.html`:
# `<button class="btn btn-secondary" onclick="if(window.volPreExpiryChart) exportChartDataToCSV(window.volPreExpiryChart, 'Vol_Pre_Expiry'); else exportChartDataToCSV(volPreExpiryChart, 'Vol_Pre_Expiry')">`
# Wait! If `volPreExpiryChart` is defined via `let volPreExpiryChart = null;` at the top level, it is NOT attached to `window` if `script_workbench2.js` is treated differently, but usually `let` at global scope is global but NOT on `window`.
# So `window.volPreExpiryChart` is `undefined`.
# The `if(window.volPreExpiryChart)` is `false`.
# Then it evaluates the `else exportChartDataToCSV(volPreExpiryChart, ...)`
# Wait, if it evaluates the `else` block, `volPreExpiryChart` will be evaluated. If it's `null`, it passes `null` to `exportChartDataToCSV`.
# `exportChartDataToCSV` will do `if (!chartInstance) { alert("Chart is not loaded or data is empty."); return; }`.
# IT WOULD ALERT.
# But what if there is a JS error before it even calls `exportChartDataToCSV`?
# E.g. `exportChartDataToCSV` is not defined?
# Or what if `exportChartDataToCSV` throws an error inside because `isChartJS` definition fails?
# No, `typeof chartInstance.config` is safe.

# The user explicitly said: "No error, its dead button".
# No console error? Or just no UI error/alert? "No error, its dead button" usually means nothing visibly happens (no alert, no download).
# Wait. `const downloadLink = document.createElement('a');`
# `downloadLink.download = filename + '.csv';`
# `downloadLink.href = window.URL.createObjectURL(csvFile);`
# Is `window.URL.createObjectURL` failing? No.
# If `exportChartDataToCSV` is NOT defined, clicking the button would throw `Uncaught ReferenceError: exportChartDataToCSV is not defined` in the console. The user might not be looking at the console.

# Let's check where `exportChartDataToCSV` is defined.
# It's in `script_workbench2.js` at line 3516.
