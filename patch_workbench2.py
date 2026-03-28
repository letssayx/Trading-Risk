import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Replace the participant rendering block in loadMarketActivity
old_code = """
        // 2. Load Participant OI Chart
        try {
            const res = await fetch(`/api/market-activity/participant-oi?days=${days}`);
            const data = await res.json();

            // Calculate Math
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
                },"""

new_code = """
        // 2. Load Participant OI Chart
        try {
            const res = await fetch(`/api/market-activity/participant-oi?days=${days}`);
            const data = await res.json();

            const partType = document.getElementById('participant-type-select') ? document.getElementById('participant-type-select').value : 'FII';
            const prefix = partType.toLowerCase();

            // Calculate Math
            let idxCurrent = 0; let stkCurrent = 0; let optIdxCurrent = 0; let optStkCurrent = 0;
            const futIdxData = data[`${prefix}_fut_idx`] || [];
            const futStkData = data[`${prefix}_fut_stk`] || [];
            const optIdxData = data[`${prefix}_opt_idx`] || [];
            const optStkData = data[`${prefix}_opt_stk`] || [];

            if (futIdxData.length > 0) {
                idxCurrent = futIdxData[futIdxData.length - 1];
                stkCurrent = futStkData[futStkData.length - 1];
                optIdxCurrent = optIdxData[optIdxData.length - 1];
                optStkCurrent = optStkData[optStkData.length - 1];
            }

            document.getElementById('participant-oi-summary').innerHTML =
                `<span style="color:${idxCurrent>=0?'#4ade80':'#ff4d4d'}">Idx Fut: ${idxCurrent.toLocaleString()}</span> | ` +
                `<span style="color:${stkCurrent>=0?'#4ade80':'#ff4d4d'}">Stk Fut: ${stkCurrent.toLocaleString()}</span> | ` +
                `<span style="color:${optIdxCurrent>=0?'#4ade80':'#ff4d4d'}">Idx Opt: ${optIdxCurrent.toLocaleString()}</span> | ` +
                `<span style="color:${optStkCurrent>=0?'#4ade80':'#ff4d4d'}">Stk Opt: ${optStkCurrent.toLocaleString()}</span>`;


            if (participantChartInstance) participantChartInstance.destroy();
            const ctx = document.getElementById('participantOiChart').getContext('2d');
            participantChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [
                        { label: 'Idx Fut Net', yAxisID: 'y', data: futIdxData, borderColor: '#36a2eb', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'Stk Fut Net', yAxisID: 'y', data: futStkData, borderColor: '#ffce56', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'Idx Opt Net', yAxisID: 'y', data: optIdxData, borderColor: '#a855f7', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'Stk Opt Net', yAxisID: 'y', data: optStkData, borderColor: '#4ade80', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 },
                        { label: 'NIFTY', yAxisID: 'y1', data: data.nifty_close, borderColor: '#ffff00', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2, borderDash: [5, 5] }
                    ]
                },"""

content = content.replace(old_code, new_code)
with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
