document.addEventListener('DOMContentLoaded', () => {
    const input = document.querySelector('.chat-input');
    const container = document.getElementById('jules-content');

    if (input) {
        input.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                const message = input.value.trim();
                if (!message) return;

                // User message
                appendMessage('You', message);
                input.value = '';

                // Jules response placeholder
                const loadingId = appendMessage('Jules', 'Thinking...');

                try {
                    // Decide endpoint based on command
                    const isCommand = message.startsWith('/');
                    const endpoint = isCommand ? '/api/jules/command' : '/api/jules/chat';

                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message })
                    });

                    const data = await response.json();

                    // Update placeholder
                    updateMessage(loadingId, data.reply || data.message || "I didn't understand that.");

                } catch (error) {
                    updateMessage(loadingId, "Error: " + error.message);
                }
            }
        });
    }

    function appendMessage(sender, text) {
        const div = document.createElement('div');
        const id = 'msg-' + Date.now();
        div.id = id;
        div.className = 'msg';
        div.innerHTML = `<strong>${sender}:</strong> ${text}`;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
        return id;
    }

    function updateMessage(id, text) {
        const div = document.getElementById(id);
        if (div) {
            div.innerHTML = `<strong>Jules:</strong> ${text}`;
        }
    }
});
