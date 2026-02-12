# AUDIT REPORT

## 1. Directory Structure Violation Analysis

Based on the scan, the current structure is:

- `backend/strategies/` contains: `turtle.py` (Class), `toolbox/` (Classes), `macro_stat_arb.py` (Functions), `vol_arb.py` (Functions), `convergence.py` (Functions).
- `backend/risk/` contains: `manager.py` (Class), `hedging.py` (Functions), `measures/` (Functions), `toolbox/` (Classes).
- `backend/analysis/` contains: `beta.py` (Functions), `greeks.py` (Functions), `sentiment_flow.py` (Functions), `toolbox/` (Classes).
- `backend/core/` contains: `toolbox/` (Classes).

**Violations Found:**

1.  **Mixed Logic**: `backend/strategies/` contains both Classes (`TurtleLegacyStrategy`) and functional scripts (`macro_stat_arb.py`, `vol_arb.py`).
2.  **Misplaced Models**: `backend/strategies/toolbox/factor_model.py` (Factor Exposure) is a Risk Model but lives in Strategies.
3.  **Misplaced Tools**: `backend/core/toolbox/math_tools.py` and `stats_tools.py` contain logic that should be in `models/` or `analysis/`.
4.  **API Logic**: `backend/web/routes.py` contains Pydantic models (`StrategyRequest`) which should be in `domain/schemas`.

## 2. Refactoring Plan (Phase 1)

**Priority 1: Strategy Files**
- Move `backend/strategies/toolbox/factor_model.py` -> `backend/risk/models/factor.py` (or similar).
- Refactor `backend/strategies/vol_arb.py` (Functions) -> `backend/strategies/vol_arb.py` (Class `VolArbitrageStrategy`).
- Refactor `backend/strategies/macro_stat_arb.py` -> `backend/strategies/macro.py` (Class `MacroStatArbStrategy`).

**Priority 2: Model Files**
- Move `backend/core/toolbox/stats_tools.py` (`StatArbAlphaEngine`, `ZScoreFilter`) -> `backend/models/stats.py`.
- Move `backend/core/toolbox/math_tools.py` (`CompoundingAuditor`) -> `backend/models/math.py`.

**Priority 3: Risk Files**
- Ensure `backend/risk/manager.py` only contains `RiskManager`.
- Move `backend/risk/toolbox/governance_tools.py` -> `backend/risk/governance.py`.

**Priority 4: API Routes**
- Move Request/Response models from `backend/web/routes.py` -> `backend/domain/web/schemas.py`.

## 3. Duplicate Code Check
- `grep` for "calculate_var" might show up in `backend/risk/measures/basel.py` and `backend/risk/toolbox/measures.py` (imports vs defs). This needs unification.

## 4. Proposed Structure (Target)

```
backend/
├── strategies/       # ONLY Strategy Classes (Turtle, VolArb, Macro)
├── models/           # ONLY Math/Stats Classes (PCA, ZScore, HMM)
├── risk/             # ONLY Risk Calculations (VaR, Governance)
├── core/             # Base Classes (BaseSovereignTool)
├── data/             # Ingestion & Adjustment
├── api/              # FastAPI Routes (thin wrappers)
└── domain/           # Schemas & Models
```
