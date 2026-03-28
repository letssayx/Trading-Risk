with open('backend/ui/static/js/rolloverTool.js', 'r') as f:
    content = f.read()

# Fix loadAggregatedData to also remove the detailed stats view if present
old_load_agg = """    loadAggregatedData: async function() {
        const tbody = document.getElementById('rollover-analysis-body');
        const dateDisplay = document.getElementById('rollover-date-display');

        if (!tbody) return;"""

new_load_agg = """    loadAggregatedData: async function() {
        const tbody = document.getElementById('rollover-analysis-body');
        const dateDisplay = document.getElementById('rollover-date-display');

        // Remove single symbol details if present
        const detailsDiv = document.getElementById('rollover-single-details');
        if (detailsDiv) {
            detailsDiv.remove();
        }

        if (!tbody) return;"""

content = content.replace(old_load_agg, new_load_agg)
with open('backend/ui/static/js/rolloverTool.js', 'w') as f:
    f.write(content)
