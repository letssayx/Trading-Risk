# Decisions

## Technology Stack
- **Language**: Python 3.11+ for backend and analytics.
- **Libraries**: NumPy, Pandas, SciPy for numerical stack.
- **Database**: PostgreSQL as the primary system of record. TimescaleDB for time-series data.
- **Visualization**: Embedded TradingView free charting widgets for frontend visualization.
- **LLM Integration**: Local, on-prem models (via Ollama or equivalent) are preferred. Remote models used for reasoning only if configured, and never access raw data.

## Architecture
- **Separation of Concerns**:
  - **Domain**: Pure business abstractions and contracts (no IO, no strategy).
  - **Analysis**: Indicator computations and market-state inference (stateless, auditable).
  - **Risk**: Risk measures, scenario definitions, and evaluation outputs.
  - **Ideas**: Trade idea objects, rationale, and validation rules (no execution).
  - **Orchestration**: Workflow composition and sequencing.
- **No Embedded Logic in UI/LLM**: Analytical logic is strictly in the Python backend. The chat layer orchestrates and explains.

## Data Management
- **Source of Truth**: PostgreSQL is the authoritative system of record.
- **Traceability**: All analytical outputs must be traceable back to their inputs (snapshots).
