# Turtle Terminal: Derivatives Analysis & Risk System

**Turtle Terminal** is a local, on-prem decision-support engine designed to quantify risk and infer market states for derivatives using deterministic logic. Like its namesake, it prioritizes a "hard shell" of capital protection before identifying opportunities.

## 🚫 Strict System Non-Goals (Boundaries)
- **No Execution**: The system must NOT contain logic to place, modify, or cancel orders. It is for Analysis only.
- **No Price Prediction**: Do not write code that "predicts" future prices. Focus only on calculating current market states (e.g., "What is the IV Rank right now?").
- **No AI-Generated Math**: All quantitative metrics (Greeks, VaR, PCR, Spreads) must be calculated using deterministic Python libraries (NumPy, Pandas). Turtle (the agent) only interprets the output.

## 🏗️ System Pillars
1.  **Risk Center**: Quantifies worst-case scenarios and probability distributions.
2.  **Market Scan Hub**: Aggregates multi-point triggers (OI, PCR, IVR) into trade ideas.
3.  **Analysis Workbench**: Host for 3D Volatility Surfaces and Ratio charts.

## 🔑 Essential Keys
- `MARKET_DATA_KEY`: Fetches live tick/OI data (Broker/Vendor API).
- `AI_ORCHESTRATOR_KEY`: Powers Turtle's reasoning (Gemini API).

## 📂 Project Structure
- `backend/`: Python FastAPI orchestrator and deterministic engines (`analysis/`, `risk/`).
- `frontend/`: React/HTML-based "Command Center" UI.
- `ingestion/`: Logic for parsing Exchange CSVs.
