# Assumptions

## System Scope & Purpose
- **Decision Support**: The system is an analysis and decision-support tool, NOT an auto-trading engine. It does not execute trades.
- **Deterministic Logic**: All numerical analysis is performed by deterministic code. Language models are used only for reasoning, explanation, and comparison.
- **Financial Correctness**: Financial correctness is prioritized over fluency or speed.
- **No Hidden Logic**: The system does not invent data or compute indicators inside language models.

## Deployment & Environment
- **Local Deployment**: The system runs entirely within a client-controlled environment (on-prem or client-owned infrastructure).
- **Data Residency**: All data (raw, derived, historical, client positions) remains within client premises. No data is sent to external services or LLMs.
- **Offline Capability**: The system is offline-capable by design and does not depend on cloud-managed backend services.

## Analysis & Risk
- **No Prediction**: The system does not predict exact prices or returns.
- **Explicit Uncertainty**: The system must be explicit about uncertainty, regime dependence, and downside risk.
- **Worst-Case Focus**: The system should highlight worst-case scenarios.
- **Chart Interpretation**: Charts are visual aids only; signals are never inferred from chart shapes.
