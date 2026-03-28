with open('backend/ui/static/js/rolloverTool.js', 'r') as f:
    content = f.read()

# Modify analyzeSingle to keep the table and put the detailed stats above or below it instead of replacing the entire resultsDiv
# Replace resultsDiv.innerHTML = html with something that inserts it above the table

old_func_start = """    analyzeSingle: async function() {
        const symbol = document.getElementById('rollover-symbol').value.toUpperCase().trim();
        const resultsDiv = document.getElementById('rollover-results');

        if (!symbol) return;

        resultsDiv.innerHTML = '<p style="text-align:center; color:#888; margin-top: 20px;">Loading Single Symbol Details...</p>';"""

new_func_start = """    analyzeSingle: async function() {
        const symbol = document.getElementById('rollover-symbol').value.toUpperCase().trim();
        let detailsDiv = document.getElementById('rollover-single-details');
        const resultsDiv = document.getElementById('rollover-results');

        if (!symbol) return;

        if (!detailsDiv) {
            detailsDiv = document.createElement('div');
            detailsDiv.id = 'rollover-single-details';
            resultsDiv.insertBefore(detailsDiv, resultsDiv.firstChild);
        }

        detailsDiv.innerHTML = '<p style="text-align:center; color:#888; margin-top: 20px;">Loading Single Symbol Details...</p>';"""

content = content.replace(old_func_start, new_func_start)

old_func_end = """            resultsDiv.innerHTML = html;

        } catch (e) {
            resultsDiv.innerHTML = `<p style="color: red; text-align:center; margin-top: 20px;">Error: ${e.message}</p>`;
        }
    },"""

new_func_end = """            detailsDiv.innerHTML = html;
            // Also filter the table to just this symbol
            this.filterData();

        } catch (e) {
            detailsDiv.innerHTML = `<p style="color: red; text-align:center; margin-top: 20px;">Error: ${e.message}</p>`;
        }
    },"""

content = content.replace(old_func_end, new_func_end)

with open('backend/ui/static/js/rolloverTool.js', 'w') as f:
    f.write(content)
