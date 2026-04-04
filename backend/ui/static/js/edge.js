const Edge = {
    init: async function() {
        await this.fetchContext();
        // Refresh every minute
        setInterval(() => this.fetchContext(), 60000);
    },

    fetchContext: async function() {
        try {
            // New endpoint for comprehensive market data
            const res = await fetch('/api/edge');
            if (res.ok) {
                const data = await res.json();
                this.render(data);
            } else {
                // Fallback to simpler stats if edge API fails
                // Or maybe fetch import stats
                const stats = await fetch('/api/v1/nse/ingest/stats');
                if (stats.ok) {
                    const sData = await stats.json();
                    this.renderFallback(sData);
                }
            }
        } catch (e) {
            console.error("Failed to fetch edge", e);
            document.getElementById('edge-content').innerText = "Context Unavailable";
        }
    },

    render: function(data) {
        const container = document.getElementById('edge-content');
        if (!data) return;

        // Determine Sentiment Color
        let sentColor = '#888';
        if (data.sentiment === 'Bullish') sentColor = '#3176B8';
        else if (data.sentiment === 'Bearish') sentColor = '#f44336';

        container.innerHTML = `
            <div style="margin-bottom:8px;"><strong>Sentiment:</strong> <span style="color:${sentColor}">${data.sentiment || 'Neutral'}</span></div>
            <div style="margin-bottom:8px;"><strong>Regime:</strong> ${data.regime || '-'}</div>
            <div style="margin-bottom:8px;"><strong>PE Ratio:</strong> ${data.pe_ratio || '-'}</div>
            <div style="margin-bottom:8px;"><strong>IV %ile:</strong> ${data.iv_percentile || '-'}</div>
            <div><strong>FII Flow:</strong> ${data.fii_flow || '-'}</div>
        `;

        // Add Import Status Indicator if available
        if (data.last_import) {
             container.innerHTML += `
                <div style="margin-top:10px; border-top:1px solid #444; pt-2; font-size:0.8em; color:#888;">
                    Last Import: ${data.last_import}
                </div>
             `;
        }
    },

    renderFallback: function(importStats) {
        const container = document.getElementById('edge-content');
        let total = 0;
        if(importStats.summary) {
            importStats.summary.forEach(s => total += s.job_count);
        }

        container.innerHTML = `
            <div style="color:#aaa;">Market data unavailable.</div>
            <div style="margin-top:10px;">
                <strong>Imports:</strong> ${total} jobs run.<br>
                <small>Check 'Import Data' for details.</small>
            </div>
        `;
    }
};

// Ensure it runs after DOM loaded, but also exposed globally for Uploader refresh
window.Edge = Edge;
document.addEventListener('DOMContentLoaded', () => Edge.init());
