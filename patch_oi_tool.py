with open('backend/ui/static/js/oiTool.js', 'r') as f:
    content = f.read()

# Fix analyzeSingle to NOT overwrite tbody with "Viewing Single Symbol History" message, but instead just filter data so it shows the row.
old_analyze_single = """    analyzeSingle: async function() {
        const symbol = document.getElementById('oi-symbol').value.toUpperCase().trim();
        const chartArea = document.getElementById('oi-chart-area');
        const tbody = document.getElementById('oi-analysis-body');

        if (!symbol) return;

        chartArea.innerHTML = 'Loading Single Symbol Analysis...';
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#888;">Viewing Single Symbol History (See Chart Above). To return to F&O view, clear search and click Refresh All.</td></tr>';

        try {
            const res = await fetch(`/api/data/analysis/oi/${symbol}`);
            if (!res.ok) throw new Error("Analysis failed");
            const data = await res.json();

            // Render Single History Plotly Chart
            this.renderSingleChart(chartArea, data);

        } catch (e) {
            chartArea.innerHTML = `<p style="color: red; padding: 20px;">Error: ${e.message}</p>`;
        }
    },"""

new_analyze_single = """    analyzeSingle: async function() {
        const symbol = document.getElementById('oi-symbol').value.toUpperCase().trim();
        const chartArea = document.getElementById('oi-chart-area');

        if (!symbol) return;

        chartArea.innerHTML = '<p style="padding: 20px; text-align: center; color: #888;">Loading Single Symbol Analysis...</p>';

        // Filter the table to just show this symbol instead of hiding it
        if (this.allData && this.allData.length > 0) {
            this.filterData();
        }

        try {
            const res = await fetch(`/api/data/analysis/oi/${symbol}`);
            if (!res.ok) throw new Error("Analysis failed");
            const data = await res.json();

            // Render Single History Plotly Chart
            this.renderSingleChart(chartArea, data);

        } catch (e) {
            chartArea.innerHTML = `<p style="color: red; padding: 20px;">Error: ${e.message}</p>`;
        }
    },"""

content = content.replace(old_analyze_single, new_analyze_single)

old_event = """            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') OiTool.analyzeSingle();
            });"""

new_event = """            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    if (input.value.trim() === '') {
                        OiTool.loadAggregatedData();
                    } else {
                        OiTool.analyzeSingle();
                    }
                }
            });
            input.addEventListener('input', (e) => {
                if (input.value.trim() === '') {
                    OiTool.loadAggregatedData();
                } else {
                    if (document.getElementById('oi-analysis-body')) {
                        OiTool.filterData();
                    }
                }
            });"""

content = content.replace(old_event, new_event)

with open('backend/ui/static/js/oiTool.js', 'w') as f:
    f.write(content)
