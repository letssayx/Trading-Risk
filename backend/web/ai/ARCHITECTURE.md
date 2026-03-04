# AI-Analyze Module Architecture (TerminalOrchestrator)

The AI-Analyze tab acts as a "Hedge Fund Terminal," enabling users to interactively query market data, run quantitative logic, and generate trading strategies via a multi-agent orchestration layer.

## Overview

The `TerminalOrchestrator` (`backend/web/ai/orchestrator.py`) handles incoming commands via WebSocket (`/ws/ai-analyze`). It splits the analysis process into a 4-step pipeline, dispatching tasks to different specialized LLM engines through three APIs (Groq, OpenRouter, Google).

```mermaid
graph TD;
    User[User Command] --> Dispatcher[Step 1: Dispatcher<br>Llama 3.3 (Groq)];
    Dispatcher --> DataClerk[Step 2: Data Clerk<br>Qwen 2.5 (OpenRouter)];
    Dispatcher --> QuantLogic[Step 3: Quant Engine<br>Llama 3.3 (Groq)];
    DataClerk --> Strategist[Step 4: Strategist<br>Gemini 1.5 Pro];
    QuantLogic --> Strategist;
    Strategist --> UI[Execution Output & DB Log];
```

## Step 1: Dispatch
- **Engine:** `llama-3.3-70b-versatile` (via Groq)
- **Purpose:** Classifies the incoming natural language command into one of 5 major trading engines: *Black Swan, Macro, Corporate Action, Derivatives, Earnings*.
- **Rationale:** Ensures downstream logic is appropriately context-aware of the event type.

## Step 2: Data Clerk (Zero Hallucination Data Extraction)
- **Engine:** `qwen/qwen-2.5-72b-instruct` (via OpenRouter)
- **Purpose:** Extracts the core stock ticker symbol or index from the user's query.
- **Data Matrix:** Once the ticker is extracted, it programmatically queries the local TimescaleDB instance (via `tools.fetch_bhavcopy_data`) to fetch the most recent End-of-Day (EOD) metrics, Futures Open Interest, and Implied Move percentage.
- **Rationale:** Prevents AI from hallucinating stock prices by grounding all analysis purely on actual database records.

## Step 3: Quant Logic Engine (Chain-of-Thought)
- **Engine:** `llama-3.3-70b-versatile` (via Groq)
- **Purpose:** Acts as the Quantitative logic engine. It uses the `<think>` tag paradigm to perform mathematical or logical step-by-step reasoning about market implications of the prompt.
- **Streaming:** This logic is streamed character-by-character back to the WebSocket so the user sees the "Chain of Thought" happen live in the terminal.

## Step 4: Strategist Synthesis
- **Engine:** `gemini-1.5-pro` (via Google GenAI SDK)
- **Purpose:** Acts as the Head Strategist. It ingests the exact numerical `Data Matrix` from Step 2 alongside the full `Quant Reasoning` output from Step 3.
- **Output:** It synthesizes a final structured execution order containing:
  - Action (e.g., ACCUMULATE ON DIPS, AGGRESSIVE SHORT)
  - Target Price
  - Stop Loss
  - Confidence Score
  - Predicted Opening Price
  - Rationale
- **Persistence:** This prediction is logged into the `import_logs` equivalent `AIPrediction` SQLAlchemy model to benchmark system accuracy over time.
