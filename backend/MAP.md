# Turtle Terminal - Master Strategy Index

This document maps all quantitative strategies to their logical implementation ("The Brain") and execution layer ("The General").

## 1. Strategy Mapping

| Strategy Component | Logic Script (The Brain) | Execution Script (The General) | Description |
| :--- | :--- | :--- | :--- |
| **Turtle Legacy** | `backend/strategies/turtle.py` | `backend/web/routes.py` (API) | 1983 Trend Following Rules (N, 2N Stops, Pyramiding). |
| **Sentiment Flow** | `backend/intelligence/sentiment.py` | `backend/strategies/convergence.py` | Smart Money Sync (FII, PCR, TRIN, OI Structure). |
| **Macro StatArb** | `backend/strategies/macro_stat_arb.py` | `backend/web/routes.py` (API) | PCA/Eigen-Beta extraction for Systematic Risk isolation. |
| **Vol Arbitrage** | `backend/strategies/vol_arb.py` | `backend/web/routes.py` (API) | Volatility Term Structure (Calendar King) & Theta/Vega Efficiency. |
| **Convergence** | `backend/strategies/convergence.py` | `backend/web/routes.py` (API) | High-Conviction Alerts (Turtle + Sentiment alignment). |
| **Hedging** | `backend/risk/hedging.py` | `backend/web/routes.py` (API) | Beta-Neutralization & Sentiment-Adjusted Index Shorting. |
| **Regime Detection** | `backend/analysis/market_state/regime.py` | `backend/risk/measures/basel.py` | HMM-based Market State Classification (Bull/Bear/Sideways). |
| **Tail Risk (EVT)** | `backend/risk/measures/evt.py` | `backend/risk/reports/alpha.py` | Extreme Value Theory (GPD/POT) for Black Swan estimation. |
| **Basel Risk** | `backend/risk/measures/basel.py` | `backend/risk/reports/alpha.py` | 500-day VaR, Standard Error, and Stressed Risk (SVaR). |

## 2. Infrastructure Mapping

| Component | Path | Purpose |
| :--- | :--- | :--- |
| **Data Models** | `backend/domain/` | SQLAlchemy Models & Pydantic Schemas. |
| **API Router** | `backend/web/routes.py` | Unified Gateway for all strategies. |
| **Reporting** | `backend/risk/reports/alpha.py` | 4:15 PM Alpha Report Generator. |
| **Intelligence** | `backend/intelligence/` | Core Sentiment & Market State logic. |
