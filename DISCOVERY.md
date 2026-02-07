# Discovery List: Logic-to-Object Conversion

Scanning existing codebase for "Logic Patterns" to refactor into the Universal Framework.

## 1. Strategies (Decision Logic)
- **Pattern:** `RolloverAnalysis.check_signals` (Basis > RFR)
  - **Proposed Object:** `backend/core/strategies/rollover.py` -> `RolloverStrategy`
- **Pattern:** `SmartMoneyPulse.check_signals` (FII Ratio > 1.5)
  - **Proposed Object:** `backend/core/strategies/smart_money.py` -> `SmartMoneyStrategy`
- **Pattern:** `PairsTrading.check_signals` (Z-Score > Entry)
  - **Proposed Object:** `backend/core/strategies/pairs.py` -> `MeanReversionStrategy`
- **Pattern:** `VolatilityArbitrage.check_signals` (IV-RV Spread)
  - **Proposed Object:** `backend/core/strategies/volatility.py` -> `VolArbStrategy`

## 2. Indicators (Value Calculation)
- **Pattern:** `RolloverAnalysis.compute_indicators` (Basis Yield)
  - **Proposed Object:** `backend/core/indicators/derivatives.py` -> `BasisYield`
- **Pattern:** `SmartMoneyPulse.compute_indicators` (FII Ratio)
  - **Proposed Object:** `backend/core/indicators/sentiment.py` -> `InstitutionalRatio`
- **Pattern:** `PairsTrading.compute_indicators` (Rolling Z-Score)
  - **Proposed Object:** `backend/core/stats/timeseries.py` -> `RollingZScore` (Stat) OR `backend/core/indicators/technical.py` -> `SpreadZScore`
- **Pattern:** `VolatilityArbitrage.compute_indicators` (IV-RV Spread)
  - **Proposed Object:** `backend/core/indicators/volatility.py` -> `IVRVSpread`

## 3. Stats (Modeling & Regression)
- **Pattern:** `RegressionSuite.run_ols` (already refactored)
  - **Enhancement:** Add `APTModel` (Multi-Factor) and `PCANalyzer` (Dimensionality Reduction).
- **Pattern:** `VolatilityForecaster` (already refactored)
  - **Enhancement:** Connect to `RiskEngine`.

## 4. Risk (Sensitivity & Loss)
- **Pattern:** `ExpectedShortfall` (Tail Mean)
  - **Proposed Object:** `backend/core/risk/metrics.py` -> `CVaR`
- **Pattern:** `ParametricVaR` (Normal Dist)
  - **Proposed Object:** `backend/core/risk/metrics.py` -> `VaR`
- **Pattern:** `SystematicHedge` (Beta Hedging)
  - **Proposed Object:** `backend/core/risk/hedging.py` -> `BetaHedge`

## 5. New Macro Objects (Requirement)
- `LiquidityCore`: DXY, Fed Rate.
- `GlobalCommodities`: LME, Precious Metals.
- `CorrelationMapping`: Global-Local Link.
