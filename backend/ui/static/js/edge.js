const Edge = {
    init: async function() {
        await this.fetchContext();
        // Refresh every minute
        setInterval(() => this.fetchContext(), 60000);
    },

    fetchContext: async function() {
        try {
            const res = await fetch('/api/edge');
            const data = await res.json();
            this.render(data);
        } catch (e) {
            console.error("Failed to fetch edge", e);
            document.getElementById('edge-content').innerText = "Context Unavailable";
        }
    },

    render: function(data) {
        const container = document.getElementById('edge-content');
        container.innerHTML = `
            <div style="margin-bottom:8px;"><strong>Sentiment:</strong> <span style="color:${data.sentiment === 'Bullish' ? '#4caf50' : '#f44336'}">${data.sentiment}</span></div>
            <div style="margin-bottom:8px;"><strong>Regime:</strong> ${data.regime}</div>
            <div style="margin-bottom:8px;"><strong>PE Ratio:</strong> ${data.pe_ratio}</div>
            <div style="margin-bottom:8px;"><strong>IV %ile:</strong> ${data.iv_percentile}</div>
            <div><strong>FII Flow:</strong> ${data.fii_flow}</div>
        `;
    }
};

document.addEventListener('DOMContentLoaded', () => Edge.init());
