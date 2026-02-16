// Trading Edge Component
// Polls /api/edge and updates DOM

document.addEventListener('DOMContentLoaded', () => {
    const pollInterval = 5000; // 5 seconds

    async function fetchEdgeData() {
        try {
            const response = await fetch('/api/edge');
            if (!response.ok) return;
            const data = await response.json();

            updateDOM('val-sentiment', data.sentiment);
            updateDOM('val-regime', data.regime);
            updateDOM('val-pe', data.index_pe);
            updateDOM('val-straddle', data.atm_straddle);
            updateDOM('val-iv', data.atm_iv + '%');

        } catch (e) {
            console.error("Edge Poll Error:", e);
        }
    }

    function updateDOM(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.innerText = value;
            // Simple color coding
            if (value === 'Bullish') el.style.color = '#4caf50';
            else if (value === 'Bearish') el.style.color = '#f44336';
            else if (value === 'Neutral') el.style.color = '#ff9800';
            else el.style.color = '#E0E2E8';
        }
    }

    // Initial fetch
    fetchEdgeData();
    // Poll
    setInterval(fetchEdgeData, pollInterval);
});
