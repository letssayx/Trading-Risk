# Jules System Handover Documentation

## 1. Project Structure Mapping

This project follows a Domain-Driven Design (DDD) with a FastAPI backend. The folder structure maps to the "System Architecture" as follows:

- **`domain/`**: Core business entities and data contracts (Contracts).
  - `instruments/`: Future, Option definitions.
  - `market/`: MarketSnapshot, Positioning, MarketState.
  - `risk/`: RiskMeasure, Scenario definitions.
  - `ideas/`: TradeIdea, TradeRationale.
- **`analysis/`**: Deterministic logic engines (The Brain).
  - `derivatives_indicators/`: `compute_flow` logic.
  - `market_state/`: `infer_state` logic.
- **`risk/`**: Risk evaluation engines.
  - `scenarios/`: `evaluate_scenario` logic (Greeks math).
  - `reports/`: `generate_risk_report` logic.
- **`ideas/`**: Trade generation logic.
  - `generation/`: `generate_trade_ideas` (The Strategy Layer).
  - `explanations/`: `compose_narrative` (The Storyteller).
- **`orchestration/`**: System coordination.
  - `pipelines/`: `Executor` class (User <-> Gemini <-> Engine).
  - `policies/`: Licensing and Audit logic.
  - `gemini/`: Mock interface and Sanitizer for Code Generation.
- **`web/`**: The Application Layer (FastAPI).
  - `main.py`: Entry point and wiring.
  - `auth/`: User authentication.
  - `chat/`: Chat API endpoints.
  - `widgets/`: Universal Widget API (`/api/widgets/data`).
  - `ingest/`: Data Ingestion endpoints.
  - `dashboard/`: Dashboard Persistence endpoints.
  - `ui/`: HTML Templates (`dashboard.html`, `report_template.html`).

## 2. Running the System

### Prerequisites
- Python 3.11+
- `pip install fastapi uvicorn pandas jinja2 python-multipart`

### Start Command
```bash
uvicorn web.main:app --reload --port 8000
```

### Access Points
- **Analysis Workbench**: `http://localhost:8000/dashboard`
- **Data Ingestion Hub**: `http://localhost:8000/ingest`
- **API Documentation**: `http://localhost:8000/docs`

## 3. Key Workflows implemented

1.  **Data Ingestion**: Upload CSV -> `web/ingest` -> Parses to `MarketSnapshot`.
2.  **Analysis**: User Chat -> `web/chat` -> `Executor` -> Mock Gemini Code Gen -> `analysis/` & `risk/` -> Result.
3.  **Risk Visualization**: `web/risk` -> Returns Scenarios & Greeks for UI.
4.  **Reporting**: `web/export` -> Generates HTML/PDF Trade Thesis.
5.  **Dashboard Persistence**: `web/dashboard` -> Save/Load JSON layouts.
6.  **Advanced Widgets**: `web/widgets` -> Serves JSON for Vol Surfaces, Scanners, and Distributions.

## 4. Next Steps for Developer

- **Database**: Spin up PostgreSQL + TimescaleDB and replace the Mock DB lists in `web/` routes with real SQL queries (use `docs/schema.sql`).
- **Gemini**: Replace `orchestration/gemini/interface.py` with actual Google Gemini API calls.
- **Frontend**: Replace the HTML templates with a React/Vue SPA if higher interactivity is needed for the 3D Surface (using Plotly.js).
