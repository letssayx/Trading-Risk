function openConfig() {
    document.getElementById('config-modal').style.display = 'block';
}

async function saveConfig() {
    const google = document.getElementById('cfg-google').value;

    await fetch('/api/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            google_api_key: google
        })
    });

    document.getElementById('config-modal').style.display = 'none';
    alert('Configuration Saved (Runtime)');
}
