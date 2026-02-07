# Core Indicators

This module contains the "Sensors" of the system.

## Mathematical Logic

### Technical Indicators
- **Price Scanner**: Calculates percentage change $R_t = \frac{P_t - P_{t-1}}{P_{t-1}}$.
- **OI Scanner**: Measures Open Interest build-up.
- **Volume Scanner**: Tracks Delivery percentage against 5-day mean.

### Sentiment Indicators
- **Institutional Sentiment**: $Ratio = \frac{FII_{Long}}{FII_{Short}}$.

### Fundamental Indicators
- **Fundamental Value**: Z-Score of PE Ratio relative to sector history.
