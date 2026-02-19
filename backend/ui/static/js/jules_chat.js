// Jules Chat Interface

// Initialize Chat
document.addEventListener('DOMContentLoaded', () => {
    const input = document.querySelector('.chat-input');
    if(input) {
        input.addEventListener('keydown', (e) => {
            if(e.key === 'Enter') {
                const msg = e.target.value.trim();
                if(msg) {
                    JulesChat.send(msg);
                    e.target.value = '';
                }
            }
        });
    }
});

const JulesChat = {
    send: async function(message) {
        this.appendMessage('User', message);
        this.scrollToBottom();

        try {
            const res = await fetch('/api/jules/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: message })
            });
            const data = await res.json();

            // Parse response for code blocks
            const parsed = this.parseResponse(data.reply);

            this.appendMessage('Jules', parsed.text);

            if (parsed.code) {
                this.updatePythonTab(parsed.code);
            }

        } catch (e) {
            this.appendMessage('System', 'Error: ' + e.message);
        }
        this.scrollToBottom();
    },

    appendMessage: function(sender, text) {
        const container = document.getElementById('jules-content');
        const div = document.createElement('div');
        div.className = 'msg';
        div.style.marginBottom = '8px';
        div.innerHTML = `<strong>${sender}:</strong> ${this.formatText(text)}`;
        container.appendChild(div);
    },

    formatText: function(text) {
        // Simple formatting: newlines to <br>
        return text.replace(/\n/g, '<br>');
    },

    parseResponse: function(rawText) {
        // Extract python code blocks
        const codeRegex = /```python\s*([\s\S]*?)\s*```/g;
        let match;
        let code = '';
        let text = rawText;

        while ((match = codeRegex.exec(rawText)) !== null) {
            code += match[1] + '\n\n';
            // Remove code from text display to avoid duplication, or keep it?
            // User said "show the code there" (python tab).
            // Usually showing in chat AND tab is fine, but maybe redundant.
            // Let's keep a reference or replace with "[Code extracted to Python Tab]"
            text = text.replace(match[0], '<em>[Code snippet sent to Python Tab]</em>');
        }

        return { text: text, code: code.trim() };
    },

    updatePythonTab: function(code) {
        const pyContainer = document.getElementById('python-content');
        // Append or replace? "show the code there".
        // Appending is safer for history.
        // Let's create a block.
        const block = document.createElement('pre');
        block.style.background = '#222';
        block.style.padding = '10px';
        block.style.border = '1px solid #444';
        block.style.overflowX = 'auto';
        block.innerText = code;

        // Add timestamp or separator
        const header = document.createElement('div');
        header.style.color = '#888';
        header.style.fontSize = '0.8em';
        header.style.marginTop = '10px';
        header.innerText = `Generated at ${new Date().toLocaleTimeString()}`;

        pyContainer.appendChild(header);
        pyContainer.appendChild(block);

        // Optionally switch tab? User might want to stay in chat.
        // Let's just notify.
        // Or switch if they asked for code.
        // "switchLeftTab" is global in workbench.html
        if (window.switchLeftTab) {
            // Maybe flash the tab?
            const pyTab = document.querySelectorAll('.tab-btn')[1]; // Python Code tab
            if(pyTab) {
                pyTab.style.color = '#00bcd4';
                setTimeout(() => pyTab.style.color = '', 2000);
            }
        }
    },

    scrollToBottom: function() {
        const container = document.getElementById('jules-content');
        container.scrollTop = container.scrollHeight;
    }
};
