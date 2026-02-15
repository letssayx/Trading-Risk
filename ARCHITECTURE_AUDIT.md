# Architecture Audit Report

This report summarizes the findings from the architecture audit of the Turtle Terminal codebase, focusing on component classification and potential duplicates.

## Component Classification Audit

### 1. Strategies (Entry/Exit Logic)
*   **Definition:** Classes or functions that define trading logic (buy/sell/exit signals).
*   **Expected Location:** `backend/strategies/`
*   **Findings:**
    *   `TurtleLegacyStrategy` (Class) -> `backend/strategies/turtle.py` (Correct)
    *   `ConvergenceStrategy` (Class) -> `backend/strategies/convergence.py` (Correct)
    *   `StatArbAlphaEngine` (Class/Tool) -> `backend/strategies/stat_arb/alpha_engine.py` (Correct)
    *   `VolArbitrageStrategy` (Class/Tool) -> `backend/strategies/vol_arb.py` (Correct)
    *   `MacroStatArbStrategy` (Class/Tool) -> `backend/strategies/macro_stat_arb.py` (Correct - though calculates PCA internally)

### 2. Filters (Signal Conditioners)
*   **Definition:** Tools that modify or filter signals based on market conditions.
*   **Expected Location:** `backend/strategies/toolbox/filters.py` or `backend/analysis/toolbox/`
*   **Findings:**
    *   `ZScoreFilter` (Class) -> `backend/strategies/toolbox/filters.py` (Correct)
    *   `InstitutionalPulse` (Class/Tool) -> `backend/analysis/toolbox/flow_tools.py` (Correct - Analysis Tool acting as a Filter/Indicator)

### 3. Indicators (Visual Overlays / Calculations)
*   **Definition:** Tools that calculate values for visualization or strategy input.
*   **Expected Location:** `backend/indicators/` (Not currently populated) or `backend/analysis/toolbox/`
*   **Findings:**
    *   `VolatilitySurfaceTool` (Class) -> `backend/analysis/toolbox/volatility_tools.py` (Correct - Analysis Tool)
    *   `SpreadSynthesizer` (Class) -> `backend/analysis/toolbox/spread_tools.py` (Correct - Analysis Tool)
    *   `FICOTool` (Class) -> `backend/analysis/toolbox/spread_tools.py` (Correct - Analysis Tool)

### 4. Risk Models (Calculations)
*   **Definition:** Tools for calculating portfolio risk (VaR, Greeks, etc.).
*   **Expected Location:** `backend/risk/measures/` or `backend/risk/models/`
*   **Findings:**
    *   `VaR` (Function `calculate_historical_var`) -> `backend/risk/measures/basel.py` (Correct - Function-based)
    *   `RiskManager` (Class) -> `backend/risk/manager.py` (Correct)
    *   `GovernanceAuditor` (Class) -> `backend/risk/governance.py` (Correct)

## Duplicate Check: InstitutionalPulse

*   **Task:** Verify if `InstitutionalPulse` exists in `indicators/` or `strategies/brushes/`.
*   **Result:**
    *   Found: `backend/analysis/toolbox/flow_tools.py`
    *   NOT Found: `backend/indicators/institutional_pulse.py`
    *   NOT Found: `backend/strategies/brushes/institutional_pulse.py`
    *   **Conclusion:** No duplicate file currently exists in the scanned directories. The single instance is correctly located in `analysis/toolbox/flow_tools.py` as it analyzes market flow (Institutional/FII activity).

## Other Potential Issues

*   **PCA Logic:** Currently resides within `backend/strategies/macro_stat_arb.py` as `calculate_pca_factors`.
    *   *Recommendation:* Consider moving `calculate_pca_factors` to `backend/analysis/toolbox/pca.py` if used by multiple strategies, but acceptable for now.
*   **ATR:** No explicit `ATRFilter` or `ATRIndicator` class found. Likely implemented as a function or missing.
