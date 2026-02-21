function openConfig() {
    document.getElementById('config-modal').style.display = 'block';
    // Clear previous status
    const status = document.getElementById('config-status');
    if (status) status.innerText = '';
}

async function saveConfig() {
    const google = document.getElementById('cfg-google').value;
    const status = document.getElementById('config-status') || createStatusElement();

    status.innerText = "Saving...";
    status.style.color = "#ccc";

    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                google_api_key: google
            })
        });

        if (res.ok) {
            status.innerText = "Configuration Saved (Runtime)";
            status.style.color = "#4caf50";
            setTimeout(() => {
                document.getElementById('config-modal').style.display = 'none';
            }, 1000);
        } else {
            throw new Error("Failed to save");
        }
    } catch (e) {
        status.innerText = "Error saving config";
        status.style.color = "#f44336";
    }
}

function createStatusElement() {
    const div = document.createElement('div');
    div.id = 'config-status';
    div.style.marginTop = '10px';
    div.style.fontSize = '0.9em';
    document.querySelector('#config-modal .modal-content').appendChild(div);
    return div;
}
