# Data Inventory Report

This report catalogs all data ingestion, storage, and processing components currently present in the Turtle Terminal codebase.

## 1. Data Upload Components

**Summary:** No direct file upload (CSV/Excel) endpoints were found in the API (`backend/web`). All data ingestion is currently handled via API requests or programmatic fetchers.

### Tick-by-Tick Data
*   **File:** `backend/ingest/tick_vault.py`
*   **Component:** `TickVault` class.
*   **Format:** Programmatic (List of Dictionaries).
*   **Database:** TimescaleDB (Stubbed).
*   **Status:** **Partial/Stub**. The class exists with methods `store_ticks` and `fetch_ticks`, but the implementation bodies are empty (`pass` or returning empty DataFrame). No actual DB connection logic is implemented.

### EOD Historical Data
*   **File:** `backend/data/loader.py`
*   **Component:** `NSEDataLoader` class.
*   **Format:** External API (NSE Website - Stub / Yahoo Finance - Working Fallback).
*   **Database:** TimescaleDB (Stubbed in `_store_ohlcv`).
*   **Status:** **Partial**. The fetch logic has a working fallback to `yfinance`, but the primary NSE scraper and the database storage logic are stubs.

### Corporate Actions (Splits/Bonuses)
*   **File:** `backend/ingest/adjustment.py`
*   **Component:** `PriceAdjuster` class.
*   **Format:** In-memory Dictionary (`self.corporate_actions`).
*   **Database:** None (In-memory).
*   **Status:** **Working Logic / No Persistence**. The logic to adjust prices based on splits is implemented, but there is no mechanism to load these actions from a file or database.

## 2. Strategy Data Components

### Smart Money / Sentiment Data
*   **File:** `backend/intelligence/sentiment_flow.py` (Logic), `backend/web/routes.py` (Endpoint).
*   **Component:** `analyze_sentiment_flow` function, `sentiment_analysis` endpoint.
*   **Format:** JSON Payload via POST (`SentimentRequest`).
*   **Fields:** `fii_net` (Float), `pcr` (Float), `trin` (Float), etc.
*   **Status:** **API-Driven**. There is no "Smart Money File" (CSV/Excel) upload. Data is expected to be pushed via API from an external source or entered manually.

### Macro / PCA Data
*   **File:** `backend/strategies/macro_stat_arb.py` (Logic), `backend/web/routes.py` (Endpoint).
*   **Component:** `calculate_pca_factors`.
*   **Format:** JSON Payload via POST (`PCARequest` containing `returns_matrix`).
*   **Status:** **API-Driven**. Expects a matrix of returns to be sent in the request body.

## 3. Missing Components (Gap Analysis)

*   **CSV/Excel Upload Endpoint:** There is no API endpoint to upload a CSV or Excel file (e.g., `POST /upload/csv`).
*   **Database Integration:** The `TimescaleDB` logic is purely aspirational comments (`# In a real impl...`). No `sqlalchemy` models or connection logic for market data were found in the scanned files.
*   **Persistence:** Corporate actions and historical data storage are not persisted to a database.
