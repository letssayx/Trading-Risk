import re

with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
    text = f.read()

# Add event listener for mr-clear-ts-btn
js_insert = """
                if (btnFetchTs) {
                    btnFetchTs.addEventListener('click', () => {
                        const sym = tsInput.value.trim().toUpperCase();
                        if(sym) loadTimeseriesData(false);
                        else alert('Enter a symbol');
                    });
                }

                const btnClearTs = document.getElementById('mr-clear-ts-btn');
                if (btnClearTs) {
                    btnClearTs.addEventListener('click', () => {
                        tsInput.value = '';
                        loadTimeseriesData(true);
                    });
                }
"""

search_js = """                if (btnFetchTs) {
                    btnFetchTs.addEventListener('click', () => {
                        const sym = tsInput.value.trim().toUpperCase();
                        if(sym) loadTimeseriesData(false);
                        else alert('Enter a symbol');
                    });
                }"""

if search_js in text:
    text = text.replace(search_js, js_insert)
    with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
        f.write(text)
    print("Added event listener for Clear button.")
else:
    print("JS Search block not found.")
