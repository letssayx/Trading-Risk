/**
 * CQG-Style Spread Builder for Turtle Terminal
 * @author Turtle Terminal Team
 */

class SpreadBuilder {
    constructor(containerId) {
        console.log('SpreadBuilder constructor called with ID:', containerId);
        this.container = document.getElementById(containerId);
        console.log('SpreadBuilder container found:', this.container);
        this.legs = [];
        this.marketPrices = {};
        this.spreadId = null;

        // Initialize with one leg by default
        this.addLeg();
        this.render();
        this.bindEvents();
        this.updateFormula();
    }

    // Event Emitter System
    events = {
        'spread:calculate': (config) => {
            // Backend calls /api/spread/calculate
            console.log('Spread calculate event:', config);
        },
        'spread:save': (config) => {
            // Backend calls /api/spread/save
            console.log('Spread save event:', config);
        },
        'spread:load': (id) => {
            // Backend calls /api/spread/load/{id}
            console.log('Spread load event:', id);
        },
        'spread:chart': (config) => {
            // Open new chart tab with spread
            console.log('Spread chart event:', config);
        }
    };

    // Available symbols for dropdown
    availableSymbols = [
        'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX',
        'BANKEX', 'NIFTYIT', 'NIFTYAUTO', 'NIFTYBANK', 'NIFTYFMCG',
        'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK'
    ];

    /**
     * Render the complete spread builder UI
     */
    render() {
        if (!this.container) {
            console.error('Render failed: Container is null');
            return;
        }
        this.container.innerHTML = `
            <div class="spread-builder">
                <div class="spread-header">
                    <h2 class="spread-title">Spread Builder</h2>
                    <div class="spread-controls">
                        <button class="add-leg-btn" id="addLegBtn">+ Add Leg</button>
                        <button class="save-spread-btn" id="saveSpreadBtn">Save Spread</button>
                    </div>
                </div>

                <div class="leg-container">
                    <div class="leg-rows" id="legRows"></div>
                </div>

                <div class="formula-display" id="formulaDisplay">
                    Loading formula...
                </div>

                <div class="spread-price" id="spreadPrice">
                    Spread Price: Calculating...
                </div>

                <div class="spread-actions">
                    <button class="load-spread-btn" id="loadSpreadBtn">Load Spread</button>
                    <button class="calculate-btn" id="calculateBtn">Calculate</button>
                </div>
            </div>
        `;

        this.renderLegs();
    }

    /**
     * Render all leg rows
     */
    renderLegs() {
        const legRowsContainer = document.getElementById('legRows');
        if (!legRowsContainer) return; // Should exist after render

        legRowsContainer.innerHTML = '';

        this.legs.forEach((leg, index) => {
            const legRow = this.createLegRow(leg, index);
            legRowsContainer.appendChild(legRow);
        });
    }

    /**
     * Create a single leg row element
     */
    createLegRow(leg, index) {
        const legRow = document.createElement('div');
        legRow.className = 'leg-row';
        legRow.dataset.index = index;

        legRow.innerHTML = `
            <select class="symbol-dropdown" data-index="${index}">
                ${this.availableSymbols.map(symbol =>
                    `<option value="${symbol}" ${leg.symbol === symbol ? 'selected' : ''}>${symbol}</option>`
                ).join('')}
            </select>

            <select class="operator-dropdown" data-index="${index}">
                <option value="+" ${leg.operator === '+' ? 'selected' : ''}>+</option>
                <option value="-" ${leg.operator === '-' ? 'selected' : ''}>-</option>
                <option value="×" ${leg.operator === '×' ? 'selected' : ''}>×</option>
                <option value="÷" ${leg.operator === '÷' ? 'selected' : ''}>÷</option>
            </select>

            <input type="number" class="multiplier-input" data-index="${index}"
                   value="${leg.multiplier}" step="0.01" min="0.01" max="10.00">

            <select class="side-dropdown" data-index="${index}">
                <option value="Buy" ${leg.side === 'Buy' ? 'selected' : ''} class="buy-side">Buy</option>
                <option value="Sell" ${leg.side === 'Sell' ? 'selected' : ''} class="sell-side">Sell</option>
            </select>

            <input type="number" class="lots-input" data-index="${index}"
                   value="${leg.lots}" min="1" max="1000">

            <button class="remove-leg-btn" data-index="${index}" ${this.legs.length <= 1 ? 'disabled' : ''}>
                ${this.legs.length > 1 ? '✕' : ''}
            </button>
        `;

        return legRow;
    }

    /**
     * Bind all event listeners
     */
    bindEvents() {
        if (!this.container) return;

        // Add leg button
        const addBtn = document.getElementById('addLegBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => {
                this.addLeg();
            });
        }

        // Save spread button
        const saveBtn = document.getElementById('saveSpreadBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.saveSpread();
            });
        }

        // Calculate button
        const calcBtn = document.getElementById('calculateBtn');
        if (calcBtn) {
            calcBtn.addEventListener('click', () => {
                this.calculateSpread();
            });
        }

        // Load spread button
        const loadBtn = document.getElementById('loadSpreadBtn');
        if (loadBtn) {
            loadBtn.addEventListener('click', () => {
                this.loadSpread();
            });
        }

        // Dynamic events for leg controls
        this.container.addEventListener('change', (e) => {
            this.handleLegChange(e);
        });

        this.container.addEventListener('input', (e) => {
            this.handleLegInput(e);
        });

        this.container.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-leg-btn')) {
                const index = parseInt(e.target.dataset.index);
                this.removeLeg(index);
            }
        });
    }

    /**
     * Handle changes to leg controls
     */
    handleLegChange(e) {
        const index = parseInt(e.target.dataset.index);
        const field = e.target.className.split('-')[0];

        if (this.legs[index]) {
            this.legs[index][field] = e.target.value;
            this.updateFormula();
            this.updateSpreadPrice();
        }
    }

    /**
     * Handle input changes (for number fields)
     */
    handleLegInput(e) {
        const index = parseInt(e.target.dataset.index);
        const field = e.target.className.split('-')[0];

        if (this.legs[index]) {
            const val = parseFloat(e.target.value);
            // Only update if valid number, otherwise keep as is or default?
            // Actually, keeping as string causes .toFixed error.
            // If NaN, default to 0 or 1 depending on field?
            if (!isNaN(val)) {
                this.legs[index][field] = val;
            } else {
               // If empty string or invalid, maybe set to 0?
               // Or handle in updateFormula to not crash.
               this.legs[index][field] = 0;
            }
            this.updateFormula();
            this.updateSpreadPrice();
        }
    }

    /**
     * Add a new leg to the spread
     */
    addLeg() {
        const newLeg = {
            symbol: this.availableSymbols[0],
            operator: '+',
            multiplier: 1.00,
            side: 'Buy',
            lots: 1
        };

        this.legs.push(newLeg);
        this.renderLegs();
        this.updateFormula();
        this.updateSpreadPrice();
    }

    /**
     * Remove a leg from the spread
     */
    removeLeg(index) {
        if (this.legs.length > 1) {
            this.legs.splice(index, 1);
            // Update indices after removal
            this.renderLegs();
            this.updateFormula();
            this.updateSpreadPrice();
        }
    }

    /**
     * Update the formula display in real-time
     */
    updateFormula() {
        const formulaDisplay = document.getElementById('formulaDisplay');
        if (!formulaDisplay) return;

        if (this.legs.length === 0) {
            formulaDisplay.textContent = 'No legs configured';
            return;
        }

        const formulaParts = this.legs.map((leg, index) => {
            const operator = index === 0 ? '' : leg.operator;
            const mult = typeof leg.multiplier === 'number' ? leg.multiplier.toFixed(2) : parseFloat(leg.multiplier).toFixed(2);
            return `${operator}(${leg.symbol} × ${mult} × ${leg.lots})`;
        });

        const formula = formulaParts.join(' ');
        formulaDisplay.textContent = `Formula: ${formula}`;
    }

    /**
     * Calculate and update the spread price
     */
    updateSpreadPrice() {
        const spreadPrice = document.getElementById('spreadPrice');
        if (!spreadPrice) return;

        if (this.legs.length === 0) {
            spreadPrice.textContent = 'Spread Price: No legs configured';
            return;
        }

        try {
            const price = this.calculateSpreadPrice(this.legs, this.marketPrices);
            spreadPrice.textContent = `Spread Price: ${price.toFixed(2)}`;
        } catch (error) {
            spreadPrice.textContent = 'Spread Price: Error calculating';
        }
    }

    /**
     * Calculate the spread price based on current configuration (CQG Style)
     */
    calculateSpreadPrice(legs, marketPrices) {
        let price = 0;

        legs.forEach((leg, index) => {
            const symbolPrice = marketPrices[leg.symbol] || 0;
            const direction = leg.side === 'Buy' ? 1 : -1;
            const positionSize = leg.multiplier * leg.lots;
            const legValue = symbolPrice * positionSize * direction;

            // Operator determines if leg is ADDED or SUBTRACTED
            // In CQG style, operators determine sign relative to the spread sum
            if (index === 0) {
                price = legValue;
            } else {
                if (leg.operator === '+' || leg.operator === '×') {
                    price = price + legValue;
                } else if (leg.operator === '-' || leg.operator === '÷') {
                    price = price - legValue;
                }
            }
        });

        return price;
    }

    /**
     * Calculate the current spread
     */
    calculateSpread() {
        const config = this.getCurrentConfig();
        this.events['spread:calculate'](config);

        // Simulate market prices for demo
        this.simulateMarketPrices();
        this.updateSpreadPrice();
    }

    /**
     * Save the current spread configuration
     */
    saveSpread() {
        const config = this.getCurrentConfig();
        this.spreadId = `SPREAD_${Date.now()}`;
        config.id = this.spreadId;

        this.events['spread:save'](config);
        alert(`Spread saved with ID: ${this.spreadId}`);
    }

    /**
     * Load a saved spread configuration
     */
    loadSpread() {
        const spreadId = prompt('Enter spread ID to load:');
        if (spreadId) {
            this.events['spread:load'](spreadId);
            // For demo purposes, load a sample spread
            this.loadSampleSpread();
        }
    }

    /**
     * Load a sample spread for demonstration
     */
    loadSampleSpread() {
        this.legs = [
            {
                symbol: 'NIFTY',
                operator: '×',
                multiplier: 1.00,
                side: 'Buy',
                lots: 1
            },
            {
                symbol: 'BANKNIFTY',
                operator: '-',
                multiplier: 2.00,
                side: 'Sell',
                lots: 2
            }
        ];

        this.renderLegs();
        this.updateFormula();
        this.updateSpreadPrice();
    }

    /**
     * Simulate market prices for demo
     */
    simulateMarketPrices() {
        this.availableSymbols.forEach(symbol => {
            this.marketPrices[symbol] = Math.random() * 100 + 10000; // Random price between 10000-10100
        });
    }

    /**
     * Get current spread configuration
     */
    getCurrentConfig() {
        return {
            id: this.spreadId,
            name: `Spread_${Date.now()}`,
            legs: [...this.legs],
            formula: this.getFormulaString(),
            created: new Date().toISOString(),
            tags: ['custom', 'user-defined']
        };
    }

    /**
     * Get the formula string representation
     */
    getFormulaString() {
        const formulaParts = this.legs.map((leg, index) => {
            const operator = index === 0 ? '' : leg.operator;
            const mult = typeof leg.multiplier === 'number' ? leg.multiplier.toFixed(2) : parseFloat(leg.multiplier).toFixed(2);
            return `${operator}(${leg.symbol} × ${mult} × ${leg.lots})`;
        });
        return formulaParts.join(' ');
    }

    /**
     * Export the current configuration
     */
    exportConfig() {
        return JSON.stringify(this.getCurrentConfig(), null, 2);
    }

    /**
     * Import a configuration
     */
    importConfig(config) {
        if (config && config.legs) {
            this.legs = [...config.legs];
            this.spreadId = config.id;
            this.renderLegs();
            this.updateFormula();
            this.updateSpreadPrice();
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SpreadBuilder;
}
