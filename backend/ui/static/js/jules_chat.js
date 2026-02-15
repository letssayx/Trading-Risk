class JulesChat {
    constructor() {
        this.chatHistory = document.getElementById('chat-history');
        this.input = document.getElementById('chat-input');

        // Attach event listeners
        if (this.input) {
            this.input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.handleMessage();
            });
        }

        // Find send button if exists (not always present in layout but good practice)
        const sendBtn = document.querySelector("button[onclick='sendChat()']");
        if (sendBtn) {
            sendBtn.onclick = () => this.handleMessage();
            // Remove inline onclick to avoid double fire if needed, or just let it override
            sendBtn.removeAttribute('onclick');
        }
    }

    async handleMessage() {
        const text = this.input.value.trim();
        if (!text) return;

        // User Message
        this.appendMessage(text, 'user');
        this.input.value = '';

        // Show Loading
        const loadingId = this.appendMessage("Analyzing request...", 'jules');

        try {
            // Call Backend
            const response = await fetch('/api/jules/parse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });

            const data = await response.json();

            // Remove Loading
            document.getElementById(loadingId).remove();

            // Show Response
            this.appendMessage("Here is the generated strategy code based on your request:", 'jules');
            this.appendCodeBlock(data.code);

            // Visualize (if StrategyComposer available)
            if (window.StrategyComposer && window.strategyComposer) {
                window.strategyComposer.loadFromCode(data.config);
                this.appendMessage("I've also visualized this in the Strategy Composer tab.", 'jules');
            }

        } catch (e) {
            document.getElementById(loadingId).innerText = "Error processing request.";
            console.error(e);
        }
    }

    async executeCode(code) {
        this.appendMessage("Executing strategy...", 'jules');

        try {
            const response = await fetch('/api/jules/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            });

            const result = await response.json();

            this.appendMessage(`Execution Result:\n${result.output}\nStatus: ${result.status}`, 'jules');

        } catch (e) {
            this.appendMessage("Execution Failed.", 'jules');
        }
    }

    appendMessage(text, sender) {
        const id = 'msg_' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = `chat-bubble ${sender}`;
        div.innerText = text;
        this.chatHistory.appendChild(div);
        this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
        return id;
    }

    appendCodeBlock(code) {
        const div = document.createElement('div');
        div.className = 'code-block';
        div.style.cssText = "background:#111; padding:10px; border-radius:4px; font-family:monospace; color:#4caf50; font-size:0.85em; margin-top:5px; white-space:pre-wrap; position:relative;";
        div.innerText = code;

        const runBtn = document.createElement('button');
        runBtn.innerText = "▶ RUN";
        runBtn.style.cssText = "position:absolute; top:5px; right:5px; background:#00bcd4; color:#000; border:none; border-radius:3px; cursor:pointer; font-weight:bold; font-size:0.8em; padding:2px 6px;";
        runBtn.onclick = () => this.executeCode(code);

        div.appendChild(runBtn);
        this.chatHistory.appendChild(div);
        this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
    }
}

// Initialize
window.onload = (function(oldLoad) {
    return function() {
        if (oldLoad) oldLoad();
        window.julesChat = new JulesChat();
    }
})(window.onload);
