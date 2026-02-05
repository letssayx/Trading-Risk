# Audit Guidelines

## Core Principles
1.  **Traceability**: Every output (Indicator, Market State, Risk Report, Trade Idea) must be traceable back to its source `MarketSnapshot` and the specific version of the code/logic used.
2.  **Determinism**: Given the same `MarketSnapshot` and configuration, the system must produce the exact same analytical output.
3.  **Separation**: Analytical logic must be separated from orchestration, UI, and explanation layers.

## Implementation Requirements
- **Immutable Inputs**: Market data snapshots should be treated as immutable once created.
- **Provenance**: `IndicatorResult` and other derived objects must include metadata about their inputs and computation context.
- **No "Black Box"**: Language models must not perform calculations. All numbers must come from the deterministic engine.
- **Explicit Reasoning**: Trade ideas must include a `TradeRationale` that links specific indicators to the proposed action.

## Verification
- **Unit Tests**: Domain invariants and auditability requirements should be verified by tests.
- **Logging**: Significant state changes and decision points in the orchestration layer should be logged.
