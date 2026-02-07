# Core Risk

This module handles Risk Metrics and Hedging Logic.

## Formulas

### Parametric VaR
$VaR_{\alpha} = \mu - z_{\alpha} \cdot \sigma$

### Expected Shortfall (CVaR)
$ES_{\alpha} = -\frac{1}{\alpha} \int_{0}^{\alpha} VaR_{\gamma} d\gamma$
(implemented as the mean of losses beyond the VaR cutoff)

### Vomma
$\text{Vomma} = \frac{\partial \text{Vega}}{\partial \sigma} = \frac{\partial^2 V}{\partial \sigma^2}$
