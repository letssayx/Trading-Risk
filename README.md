# Derivatives Analysis & Risk System

This system is designed to analyze derivatives markets, infer market state, quantify risk, and propose trade ideas. It acts as a decision-support system, not an auto-trading engine.

## Architecture

The system follows a domain-driven design with clear separation of concerns:
- `domain/`: Core business abstractions and contracts (Instruments, Market Snapshots, Indicators, Risk Measures, Trade Ideas).
- `analysis/`: Analytical logic for computing indicators and market state.
- `risk/`: Risk evaluation engine and scenario analysis.
- `ideas/`: Trade idea generation and validation logic.
- `orchestration/`: Workflow management.

## Documentation

See `docs/` for detailed documentation:
- [Glossary](docs/glossary.md)
- [Assumptions](docs/assumptions.md)
- [Decisions](docs/decisions.md)
- [Audit Guidelines](docs/audit-guidelines.md)

## Development

- Python 3.11+ is required.
- Run tests using `pytest` (once added).
