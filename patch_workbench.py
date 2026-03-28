with open("backend/ui/templates/workbench.html", "r") as f:
    content = f.read()

# Replace the Chart configuration for Participant OI Chart
old_chart = """            // Calculate Math
            let fiiCurrent = 0; let proCurrent = 0;
            if (data.fii_net_long && data.fii_net_long.length > 0) fiiCurrent = data.fii_net_long[data.fii_net_long.length - 1];
            if (data.pro_net_long && data.pro_net_long.length > 0) proCurrent = data.pro_net_long[data.pro_net_long.length - 1];

            document.getElementById('participant-oi-summary').innerHTML =
                `<span style="color:${fiiCurrent>=0?'#4ade80':'#ff4d4d'}">FII OI: ${fiiCurrent.toLocaleString()}</span> | <span style="color:${proCurrent>=0?'#4ade80':'#ff4d4d'}">PRO OI: ${proCurrent.toLocaleString()}</span>`;


            if (participantChartInstance) participantChartInstance.destroy();
            const ctx = document.getElementById('participantOiChart').getContext('2d');
            participantChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [
                        { label: 'FII Net Long', yAxisID: 'y', data: data.fii_net_long, borderColor: '#36a2eb', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'PRO Net Long', yAxisID: 'y', data: data.pro_net_long, borderColor: '#ffce56', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'Client Net Long', yAxisID: 'y', data: data.client_net_long, borderColor: '#a855f7', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 }, // Changed to purple to distinguish from FII
                        { label: 'NIFTY', yAxisID: 'y1', data: data.nifty_close, borderColor: '#ffff00', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2, borderDash: [5, 5] }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    scales: {
                        x: { grid: { display: false } },
                        y: { position: 'left', grid: { color: '#333' } },
                        y1: { type: 'linear', position: 'right', display: true, grid: { drawOnChartArea: false }, beginAtZero: false } // ensure NIFTY scales properly
                    },
                    plugins: { legend: { labels: { color: '#ccc' } } }
                }
            });"""

new_chart = """            // Calculate Math
            let fiiIdxCurrent = 0; let fiiStkCurrent = 0; let fiiOptIdxCurrent = 0; let fiiOptStkCurrent = 0;
            if (data.fii_fut_idx && data.fii_fut_idx.length > 0) {
                fiiIdxCurrent = data.fii_fut_idx[data.fii_fut_idx.length - 1];
                fiiStkCurrent = data.fii_fut_stk[data.fii_fut_stk.length - 1];
                fiiOptIdxCurrent = data.fii_opt_idx[data.fii_opt_idx.length - 1];
                fiiOptStkCurrent = data.fii_opt_stk[data.fii_opt_stk.length - 1];
            }

            document.getElementById('participant-oi-summary').innerHTML =
                `<span style="color:${fiiIdxCurrent>=0?'#4ade80':'#ff4d4d'}">Idx Fut: ${fiiIdxCurrent.toLocaleString()}</span> | ` +
                `<span style="color:${fiiStkCurrent>=0?'#4ade80':'#ff4d4d'}">Stk Fut: ${fiiStkCurrent.toLocaleString()}</span> | ` +
                `<span style="color:${fiiOptIdxCurrent>=0?'#4ade80':'#ff4d4d'}">Idx Opt: ${fiiOptIdxCurrent.toLocaleString()}</span> | ` +
                `<span style="color:${fiiOptStkCurrent>=0?'#4ade80':'#ff4d4d'}">Stk Opt: ${fiiOptStkCurrent.toLocaleString()}</span>`;


            if (participantChartInstance) participantChartInstance.destroy();
            const ctx = document.getElementById('participantOiChart').getContext('2d');
            participantChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [
                        { label: 'Idx Fut Net', yAxisID: 'y', data: data.fii_fut_idx, borderColor: '#36a2eb', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'Stk Fut Net', yAxisID: 'y', data: data.fii_fut_stk, borderColor: '#ffce56', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'Idx Opt Net', yAxisID: 'y', data: data.fii_opt_idx, borderColor: '#a855f7', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'Stk Opt Net', yAxisID: 'y', data: data.fii_opt_stk, borderColor: '#4ade80', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'NIFTY', yAxisID: 'y1', data: data.nifty_close, borderColor: '#ffff00', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2, borderDash: [5, 5] }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    scales: {
                        x: { grid: { display: false } },
                        y: { position: 'left', grid: { color: '#333' } },
                        y1: { type: 'linear', position: 'right', display: true, grid: { drawOnChartArea: false }, min: function(context) {
                             const dataArr = context.chart.data.datasets.find(d => d.yAxisID === 'y1').data;
                             const minVal = Math.min(...dataArr.filter(v => v > 0));
                             return minVal * 0.99; // 1% padding below min
                        }, max: function(context) {
                             const dataArr = context.chart.data.datasets.find(d => d.yAxisID === 'y1').data;
                             const maxVal = Math.max(...dataArr.filter(v => v > 0));
                             return maxVal * 1.01; // 1% padding above max
                        } } // explicit min/max to ensure NIFTY scales properly
                    },
                    plugins: { legend: { labels: { color: '#ccc' } } }
                }
            });"""

content = content.replace(old_chart, new_chart)
with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(content)
