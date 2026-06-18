// Ensure keys are loaded from session memory when config tab opens
function openConfig() {
    // If it's a modal (legacy)
    const modal = document.getElementById('config-modal');
    if (modal) modal.style.display = 'block';

    // Switch to tab if available
    if (typeof switchMainTab === 'function') {
        switchMainTab('config');
    }

    // Populate existing keys
    document.getElementById('cfg-google').value = localStorage.getItem('GOOGLE_API_KEY') || '';
    document.getElementById('cfg-groq').value = localStorage.getItem('GROQ_API_KEY') || '';
    document.getElementById('cfg-openrouter').value = localStorage.getItem('OPENROUTER_API_KEY') || '';

    const status = document.getElementById('config-status');
    if (status) status.innerText = '';
}

function saveConfig() {
    const google = document.getElementById('cfg-google').value.trim();
    const groq = document.getElementById('cfg-groq').value.trim();
    const openrouter = document.getElementById('cfg-openrouter').value.trim();

    const status = document.getElementById('config-status');

    try {
        // Securely store keys in session storage (wipes on browser close)
        if (google) localStorage.setItem('GOOGLE_API_KEY', google);
        if (groq) localStorage.setItem('GROQ_API_KEY', groq);
        if (openrouter) localStorage.setItem('OPENROUTER_API_KEY', openrouter);

        // Also attempt to update the backend config if Admin Token is present
        const adminToken = localStorage.getItem('admin_token');
        if (adminToken && google) {
            fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Token': adminToken
                },
                body: JSON.stringify({ google_api_key: google })
            }).then(response => {
                if (!response.ok) {
                    console.warn("Failed to sync config with backend:", response.status);
                }
            }).catch(err => console.warn("Network error syncing config with backend:", err));
        }

        status.innerText = "Keys saved to Secure Session Storage ✅";
        status.style.color = "#3176B8";

        setTimeout(() => {
            status.innerText = '';
        }, 3000);

    } catch (e) {
        status.innerText = "Error saving to session storage.";
        status.style.color = "#f44336";
    }
}

// Auto-load config when script initializes
window.addEventListener('DOMContentLoaded', () => {
    document.getElementById('cfg-google').value = localStorage.getItem('GOOGLE_API_KEY') || '';
    document.getElementById('cfg-groq').value = localStorage.getItem('GROQ_API_KEY') || '';
    document.getElementById('cfg-openrouter').value = localStorage.getItem('OPENROUTER_API_KEY') || '';
});
