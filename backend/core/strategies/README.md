# Core Strategies

This module contains the "Recipes" that coordinate Indicators to generate signals.

## Architecture
Strategies allow **Component Injection**.
Example: `QuadrantStrategy` takes `PriceScanner` and `OIScanner` as inputs.

## Logic
- **Rollover Basis**: $Yield = \frac{Fut - Spot}{Spot} \times \frac{365}{DTE}$
- **Pairs Trading**: $Z = \frac{Spread - \mu}{\sigma}$
