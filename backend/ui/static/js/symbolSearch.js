const SymbolSearch = {
    callback: null,

    init: function() {
        const input = document.getElementById('symbol-search-input');
        input.addEventListener('input', (e) => this.search(e.target.value));
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.close();
        });
    },

    open: function(cb) {
        this.callback = cb;
        document.getElementById('symbol-search-modal').style.display = 'flex';
        document.getElementById('symbol-search-input').value = '';
        document.getElementById('symbol-search-input').focus();
        document.getElementById('search-results').innerHTML = '';
    },

    close: function() {
        document.getElementById('symbol-search-modal').style.display = 'none';
        this.callback = null;
    },

    search: async function(query) {
        if (query.length < 2) return;
        try {
            const res = await fetch(`/api/symbols/search?q=${query}`);
            const results = await res.json();
            this.renderResults(results);
        } catch (e) {
            console.error(e);
        }
    },

    renderResults: function(results) {
        const container = document.getElementById('search-results');
        container.innerHTML = '';
        results.forEach(sym => {
            const div = document.createElement('div');
            div.className = 'search-item';
            div.innerText = sym;
            div.onclick = () => {
                if (this.callback) this.callback(sym);
                this.close();
            };
            container.appendChild(div);
        });
    }
};

// Auto-init if DOM ready, or call explicitly
document.addEventListener('DOMContentLoaded', () => SymbolSearch.init());
