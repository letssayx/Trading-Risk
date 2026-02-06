# Unified Model Entry Point
# Importing specialized models to expose them under backend.domain.models
from backend.domain.market.models import Instrument, MarketData, Base as MarketBase
from backend.strategies.models import Strategy, Base as StrategyBase
from backend.risk.models import Trade, RiskSnapshot, Base as RiskBase

# Common Base if needed, or simply exposing classes
# Note: In a real app, merging declarative bases is tricky if not shared initially.
# Here we expose the classes for easy import.
