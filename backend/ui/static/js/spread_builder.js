class SpreadBuilder {
    constructor() {
        this.formulaInput = document.getElementById('formula-input');
        this.spreadValue = document.getElementById('spread-value');
        this.watchlist = document.getElementById('watchlist-list');

        // Mock Data
        this.marketData = {
            'NIFTY': 22000.50,
            'BANKNIFTY': 46500.20,
            'RELIANCE': 2900.00,
            'HDFCBANK': 1450.00,
            'INFY': 1600.00,
            'TCS': 3900.00
        };

        this.init();
    }

    init() {
        this.renderWatchlist();
        // Make global for onclick handlers in HTML
        window.insertToken = (token) => this.insertToken(token);
        window.calculateSpread = () => this.calculate();
        window.clearFormula = () => this.clear();

        // Auto-calc on input
        this.formulaInput.addEventListener('input', () => this.calculate());
    }

    renderWatchlist() {
        this.watchlist.innerHTML = '';
        for (const [symbol, price] of Object.entries(this.marketData)) {
            const div = document.createElement('div');
            div.className = 'symbol-item';
            div.innerHTML = `<span>${symbol}</span><span class="symbol-price">${price.toFixed(2)}</span>`;
            div.onclick = () => this.insertToken(symbol);
            this.watchlist.appendChild(div);
        }
    }

    insertToken(token) {
        const current = this.formulaInput.value;
        // Simple append, in prod use cursor position
        // Add space around operators for readability if needed, but for now strict append
        if (['+', '-', '*', '/'].includes(token)) {
            this.formulaInput.value = current + ' ' + token + ' ';
        } else {
            this.formulaInput.value = current + token;
        }
        this.calculate();
        this.formulaInput.focus();
    }

    clear() {
        this.formulaInput.value = '';
        this.spreadValue.innerText = '--';
    }

    calculate() {
        const expression = this.formulaInput.value;
        if (!expression.trim()) {
            this.spreadValue.innerText = '--';
            return;
        }

        try {
            // 1. Tokenize and replace symbols with prices
            // Regex to find words that match market data keys
            let evalExpr = expression;

            // Sort keys by length desc to avoid replacing substring (e.g. NIFTY vs NIFTYBANK)
            // But here NIFTYBANK contains NIFTY, so order matters.
            const symbols = Object.keys(this.marketData).sort((a,b) => b.length - a.length);

            for (const sym of symbols) {
                const price = this.marketData[sym];
                // Replace whole word only
                const regex = new RegExp(`\\b${sym}\\b`, 'g');
                evalExpr = evalExpr.replace(regex, price);
            }

            // 2. Safety Check: Only allow numbers, operators, parens, spaces
            if (!/^[\d\.\s\+\-\*\/\(\)]+$/.test(evalExpr)) {
                throw new Error("Invalid characters");
            }

            // 3. Eval (Safe-ish due to regex check above)
            // Function constructor is slightly safer than direct eval but still...
            // In strict prod, use a math parser library like mathjs
            const result = new Function('return ' + evalExpr)();

            if (isNaN(result) || !isFinite(result)) {
                this.spreadValue.innerText = "Error";
                this.spreadValue.style.color = "#f44336";
            } else {
                this.spreadValue.innerText = result.toFixed(2);
                this.spreadValue.style.color = result >= 0 ? "#4CAF50" : "#f44336";
            }

        } catch (e) {
            console.warn("Calc Error:", e);
            this.spreadValue.innerText = "Error";
            this.spreadValue.style.color = "#f44336";
        }
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    new SpreadBuilder();
});
