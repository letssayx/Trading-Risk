// Symbol Search Modal
// Reusable component

class SymbolSearch {
    constructor() {
        this.createModal();
    }

    createModal() {
        this.modal = document.createElement('div');
        this.modal.style.cssText = "position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:1000; display:none; justify-content:center; align-items:center;";
        this.modal.innerHTML = `
            <div style="background:#25262D; padding:20px; width:300px; border:1px solid #444; border-radius:4px;">
                <h3 style="margin-top:0; color:#eee;">Select Symbol</h3>
                <input type="text" id="sym-search-input" placeholder="Search..." style="width:100%; padding:8px; background:#111; border:1px solid #333; color:#fff; margin-bottom:10px;">
                <div id="sym-results" style="max-height:150px; overflow-y:auto; border:1px solid #333; margin-bottom:10px;"></div>
                <div style="display:flex; justify-content:flex-end; gap:10px;">
                    <button onclick="window.symbolSearch.close()" style="background:transparent; border:1px solid #444; color:#aaa; padding:4px 10px; cursor:pointer;">Cancel</button>
                </div>
            </div>
        `;
        document.body.appendChild(this.modal);

        const input = this.modal.querySelector('#sym-search-input');
        input.addEventListener('input', (e) => this.doSearch(e.target.value));
    }

    open(callback) {
        this.callback = callback;
        this.modal.style.display = 'flex';
        this.modal.querySelector('input').focus();
        this.doSearch('');
    }

    close() {
        this.modal.style.display = 'none';
        this.callback = null;
    }

    async doSearch(q) {
        const res = await fetch(`/api/symbols/search?q=${q}`);
        const results = await res.json();

        const container = this.modal.querySelector('#sym-results');
        container.innerHTML = '';

        results.forEach(sym => {
            const div = document.createElement('div');
            div.innerText = sym;
            div.style.cssText = "padding:6px; cursor:pointer; border-bottom:1px solid #222; font-size:0.9em; color:#ccc;";
            div.onmouseover = () => div.style.background = '#333';
            div.onmouseout = () => div.style.background = 'transparent';
            div.onclick = () => {
                if (this.callback) this.callback(sym);
                this.close();
            };
            container.appendChild(div);
        });
    }
}

window.symbolSearch = new SymbolSearch();
