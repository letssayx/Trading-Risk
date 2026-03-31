# The only issue is if `exportTableToCSV` fails because the table ID is wrong or the function doesn't work.
# The user specifically said: "not a single existing CSV that you provided download anything ... No error, its dead button".
# If I had added `<button ... onclick="exportTableToCSV('marketwatch-table', 'Basis_Watch')">` previously, and it didn't work, maybe `exportTableToCSV` itself is broken!
# Let's inspect `exportTableToCSV` in `script_workbench2.js`
with open("backend/ui/static/js/script_workbench2.js", "r") as f:
    js = f.read()

idx = js.find('function exportTableToCSV')
print(js[idx:idx+800])
