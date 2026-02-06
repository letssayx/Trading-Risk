import pandas as pd
from typing import Dict, Any
from backend.strategies.base_strategy import BaseStrategy

class StrategyEngine:
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}

    def add_strategy(self, strategy_obj: BaseStrategy):
        self.strategies[strategy_obj.name] = strategy_obj

    def run(self, ticker: str, df: pd.DataFrame, current_inventory: Dict[str, Any], overrides: Dict[str, Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main execution loop for a specific ticker.
        df: The DataFrame from your Upstox import (OHLC).
        current_inventory: Dictionary of current holdings.
        overrides: Dictionary mapping strategy_name -> {param_key: new_value}
        """
        results = {}
        overrides = overrides or {}

        for name, strategy in self.strategies.items():
            # Apply overrides if they exist for this strategy
            original_config = strategy.config.copy()
            if name in overrides:
                strategy.config.update(overrides[name])

            try:
                # 1. Enrich data with indicators
                # Using .copy() to prevent one strategy from polluting another's data context
                processed_df = strategy.compute_indicators(df.copy())

                # 2. Extract signal
                signal = strategy.check_signals(processed_df, current_inventory.get(ticker, {}))

                # 3. Add to results
                results[name] = {
                    "signal": signal,
                    "indicators": processed_df.iloc[-1].to_dict(), # Latest values
                    "active_config": strategy.config.copy()
                }
            finally:
                # Restore original config to ensure statelessness across runs
                strategy.config = original_config

        return results
