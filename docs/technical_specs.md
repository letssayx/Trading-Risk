# Technical Specifications: Jules Derivatives Analysis System

This document serves as the blueprint for the "Jules" system—a secure, local, multi-user terminal that uses AI for reasoning but keeps data private.

## 1. System Architecture Overview
The system follows a "Disconnected Intelligence" model:
- **The Brain (Local)**: Python 3.11+ backend managing the Deterministic Engine (Math/Logic).
- **The Reasoner (Cloud/Local API)**: Gemini 3 Flash (or equivalent), restricted to returning Python Code only.
- **The Database**: PostgreSQL with TimescaleDB extension for high-performance historical data storage.

## 2. Front-End: "The Workbench"
- **Tech Stack**: React.js / Vue.js (or Server-Side Templates with HTMX/Jinja2 for MVP).
- **Modular Grid**: Users can drag, resize, and save widgets (Charts, Heatmaps, Risk Tables).
- **Persistence**: Every layout change is saved to the `dashboard_templates` table via a JSONB config.
- **The Jules Sidebar**: A persistent chat window that sends user prompts to the backend and renders the returned "Story" and "PDF Export" buttons.
- **Data Ingestion Hub**: A dedicated page for drag-and-drop file uploads with a mapping interface.

## 3. Back-End: "The Orchestrator"
- **Tech Stack**: FastAPI (Python).
- **Secure Execution Sandbox**: A module that receives Python code from Gemini, verifies it against a whitelist (`analysis/`, `risk/`), and executes it locally.
- **Multi-User Licensing**: Middleware checks for a local `license.key` file and validates user sessions.
- **Audit Logging**: Every interaction (User Prompt -> Gemini Code -> Execution Result) is logged in `Gemini_Audit`.

## 4. Required Database Schema
Core tables required:
1.  **Market_Data**: TimescaleDB hypertable for price/OI/volume.
2.  **Positioning_Data**: For participant-wise (FII/Pro) historical records.
3.  **Dashboard_Templates**: To store user-defined UI layouts.
4.  **Gemini_Audit**: For tracking all AI-generated logic.
5.  **Users/Auth**: For multi-user access control.

## 5. Output Deliverables
The system must generate:
- **PDF Report**: A "Trade Thesis" document containing the story, charts, and risk scenarios.
- **Excel Export**: A raw data dump of indicators.
- **Dashboard Screenshot**: High-resolution capture of the active workbench.
