import re

with open('backend/ui/static/js/rolloverTool.js', 'r') as f:
    content = f.read()

# Replace loadSectoralChart function
# We will fetch from /api/data/analysis/rollover/sectors

chart_func = """
    loadSectoralChart: async function() {
        try {
            const res = await fetch('/api/data/analysis/rollover/sectors');
            if (!res.ok) return;
            const json = await res.json();
            const data = json.data || [];

            if (data.length === 0) return;

            const sectors = data.map(d => d.sector);
            const exp1Vals = data.map(d => d.exp1_roll);
            const exp2Vals = data.map(d => d.exp2_roll);
            const exp1Label = data[0].exp1 || 'Expiry 1';
            const exp2Label = data[0].exp2 || 'Expiry 2';

            const trace1 = {
                x: sectors,
                y: exp1Vals,
                name: exp1Label,
                type: 'bar',
                marker: { color: '#00bcd4' }, // Solid Bloomberg Cyan/Blue
                text: exp1Vals.map(v => v.toFixed(1) + '%'),
                textposition: 'auto'
            };

            const trace2 = {
                x: sectors,
                y: exp2Vals,
                name: exp2Label,
                type: 'bar',
                marker: { color: '#3176B8' }, // Standard Blue
                text: exp2Vals.map(v => v.toFixed(1) + '%'),
                textposition: 'auto'
            };

            const layout = {
                barmode: 'group',
                bargap: 0.1,
                bargroupgap: 0.0,
                paper_bgcolor: '#222',
                plot_bgcolor: '#222',
                font: { color: '#ccc' },
                margin: { t: 10, b: 60, l: 40, r: 10 },
                xaxis: { tickangle: -45 },
                yaxis: { title: 'Rollover %' },
                legend: { orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center' }
            };

            Plotly.newPlot('rollover-sector-chart', [trace2, trace1], layout, {responsive: true}); // older expiry first

        } catch(e) {
            console.error("Failed to load sectoral chart", e);
        }
    },
"""

# Find and replace the existing function
start_idx = content.find("loadSectoralChart: async function() {")
if start_idx != -1:
    end_idx = content.find("updateDynamicChart: async function() {", start_idx)
    content = content[:start_idx] + chart_func + "\n    " + content[end_idx:]

    with open('backend/ui/static/js/rolloverTool.js', 'w') as f:
        f.write(content)
    print("Patched left chart.")
else:
    print("Could not find loadSectoralChart.")
