class SpreadBuilder {
    constructor() {
        this.formulaInput = document.getElementById('formula-input');
        this.spreadValue = document.getElementById('spread-value');
        this.watchlist = document.getElementById('watchlist-list');
        this.chartArea = document.getElementById('spread-chart-area');
        this.chartCanvas = document.getElementById('chart-canvas');

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

        // Chart buttons
        document.getElementById('plot-chart-btn').addEventListener('click', () => this.plotChart());
        document.getElementById('add-indicator-btn').addEventListener('click', () => this.addIndicator());
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
            let evalExpr = expression;
            const symbols = Object.keys(this.marketData).sort((a,b) => b.length - a.length);

            for (const sym of symbols) {
                const price = this.marketData[sym];
                const regex = new RegExp(`\\b${sym}\\b`, 'g');
                evalExpr = evalExpr.replace(regex, price);
            }

            if (!/^[\d\.\s\+\-\*\/\(\)]+$/.test(evalExpr)) {
                throw new Error("Invalid characters");
            }

            const result = new Function('return ' + evalExpr)();

            if (isNaN(result) || !isFinite(result)) {
                this.spreadValue.innerText = "Error";
                this.spreadValue.style.color = "#f44336";
            } else {
                this.spreadValue.innerText = result.toFixed(2);
                this.spreadValue.style.color = result >= 0 ? "#3176B8" : "#f44336";
            }

        } catch (e) {
            console.warn("Calc Error:", e);
            this.spreadValue.innerText = "Error";
            this.spreadValue.style.color = "#f44336";
        }
    }

    plotChart() {
        // Stub for charting logic
        const formula = this.formulaInput.value;
        if (!formula) return;

        this.chartCanvas.innerHTML = `
            <div style="text-align:center;">
                <div style="font-size:1.2em; color:#fff; margin-bottom:10px;">Chart: ${formula}</div>
                <div style="width:100%; height:300px; background:#222; position:relative; display:flex; align-items:center; justify-content:center;">
                    <!-- Placeholder for Lightweight Charts -->
                    <span style="color:#666;">(Chart Visualization Placeholder)</span>
                </div>
            </div>
        `;
        console.log("Plotting chart for:", formula);
    }

    addIndicator() {
        const indicatorName = prompt("Enter Indicator Name (e.g. SMA, RSI):");
        if (indicatorName) {
            alert(`Added ${indicatorName} to Spread Chart`);
            // In real impl, would overlay indicator on chart
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new SpreadBuilder();
});
