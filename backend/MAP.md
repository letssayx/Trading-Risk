# Turtle Terminal - Master Strategy Index

This document maps all quantitative strategies to their logical implementation ("The Brain") and execution layer ("The General").

## 1. Strategy Mapping

| Strategy Component | Logic Script (The Brain) | Execution Script (The General) | Description |
| :--- | :--- | :--- | :--- |
| **Turtle Legacy** | `backend/strategies/turtle.py` | `backend/web/routes.py` (API) | 1983 Trend Following Rules (N, 2N Stops, Pyramiding). |
| **Sentiment Flow** | `backend/intelligence/sentiment_flow.py` | `backend/strategies/convergence.py` | Smart Money Sync (FII, PCR, TRIN, OI Structure). |
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
| **Security** | `backend/infrastructure/security.py` | TOTP & Session Management (Mock). |
| **Latency Monitor** | `backend/infrastructure/heartbeat.py` | Data Ingestion Health Check. |
| **Backtest Engine** | `backend/backtest/engine.py` | Strategy Simulator with Transaction Costs (Slippage/STT). |
| **Portfolio Mgr** | `backend/domain/portfolio/manager.py` | Multi-Portfolio NAV & Greek Aggregation. |
| **Workspaces** | `backend/domain/user/workspace.py` | Persistent Layout Configurations. |
| **Registry** | `backend/infrastructure/registry.py` | Master Toolbox Registry (Auto-Discovery). |

## 3. Modular Toolbox (Standalone Objects)

| Toolbox Category | Independent Object Location | Standard "OOTB" Implementation |
| :--- | :--- | :--- |
| **Scoring (Rubric)** | `backend/intelligence/toolbox/rubric.py` | `StandardAlphaScorecard` |
| **Regime (HMM)** | `backend/analysis/market_state/regime.py` | `DefaultMarketWeatherHMM` (via `RegimeDetector`) |
| **Risk Metrics** | `backend/risk/toolbox/measures.py` | `BaselVaR_500D` (via utility functions) |
| **Strategy Logic** | `backend/strategies/toolbox/library.py` | `TurtleLegacyStrategy`, `VolArbitrageStrategy` |
| **Math Utils** | `backend/core/toolbox/math_tools.py` | `CompoundingAuditor` |
| **StatArb** | `backend/core/toolbox/stats_tools.py` | `StatArbAlphaEngine` |
| **Vol Analysis** | `backend/analysis/toolbox/volatility_tools.py` | `VolatilitySurfaceTool` |
| **Inst. Flow** | `backend/analysis/toolbox/flow_tools.py` | `InstitutionalPulse` |
| **Governance** | `backend/risk/toolbox/governance_tools.py` | `GovernanceAuditor` |

## 4. Sovereign Toolbox Mapping (Sovereign Workbench)

| Modular Tool | Logic Origin | UI Brick Name |
| :--- | :--- | :--- |
| **Nifty Daily Sync** | `backend/ingest/toolbox/data_gateway.py` | `Data Gateway` |
| **HMM Regime** | `backend/analysis/market_state/regime.py` | `Market Weather` |
| **Risk Governance** | `backend/risk/toolbox/governance_tools.py` | `Governance Auditor` |
| **Smart Money** | `backend/analysis/toolbox/flow_tools.py` | `Institutional Pulse` |
| **Factor Model** | `backend/strategies/toolbox/factor_model.py` | `Factor Exposure Model` |
| **Turtle N-Calc** | `backend/strategies/toolbox/turtle_suite.py` | `Turtle N-Calc` |
| **Turtle Stop** | `backend/strategies/toolbox/turtle_suite.py` | `Turtle 2N Stop` |
