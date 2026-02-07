# Core Stats (QuantLib)

Statistical models for Volatility and Time Series analysis.

## Models

### GARCH(1,1) Proxy
$\sigma^2_t = \omega + \alpha \epsilon^2_{t-1} + \beta \sigma^2_{t-1}$
(Simulated via exponential decay weights in `VolatilityForecaster`)

### Regression (OLS)
$y = \beta X + \epsilon$

### Arbitrage Pricing Theory (APT)
$R_i = \alpha + \sum_{j=1}^{k} \beta_{ij} F_j + \epsilon_i$
Calculates sensitivity to multiple macro factors.

### Principal Component Analysis (PCA)
Decomposes covariance matrix $\Sigma$ into Eigenvalues $\lambda$ and Eigenvectors $v$ ($ \Sigma v = \lambda v $) to find primary market drivers.
