import pandas as pd
import numpy as np
from typing import Dict, Any, List

class BacktestEngine:
    def __init__(self, start_date: str, end_date: str, initial_capital: float = 1000000.0):
        self.start_date = start_date
        self.end_date = end_date
        self.capital = initial_capital
        self.current_capital = initial_capital
        self.trade_log: List[Dict[str, Any]] = []
        self.daily_returns: List[float] = []

    def run_simulation(self, strategy_config: Dict[str, Any], historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Iterates through historical bars to simulate trade signals.
        """
        # Sort by date
        historical_data = historical_data.sort_values('date')

        formula_trigger = strategy_config.get('formula_trigger', 'close > vwap')
        initial_capital_state = self.current_capital

        for index, row in historical_data.iterrows():
            # 1. Evaluate Formula (Mock)
            signal_triggered = False
            if formula_trigger == 'close > vwap':
                signal_triggered = row['close'] > row.get('vwap', row['close'])
            elif formula_trigger == 'RSI > 70':
                signal_triggered = row.get('rsi', 50) > 70

            # 2. Execute Trade
            if signal_triggered:
                # Risk Check (Mock evaluate_scenario)
                potential_risk = -0.10 * self.current_capital * 0.1

                if abs(potential_risk) <= strategy_config.get('max_risk_per_trade', 50000):
                    # Simulate Trade Outcome
                    pnl = row.get('next_day_return', 0.0) * self.current_capital * 0.1
                    self.current_capital += pnl
                    self.trade_log.append({
                        "date": row['date'],
                        "pnl": pnl,
                        "rationale": f"Triggered by {formula_trigger}",
                        "capital_after": self.current_capital
                    })

            # Record Daily State
            if initial_capital_state > 0:
                self.daily_returns.append((self.current_capital - initial_capital_state) / initial_capital_state)
            else:
                self.daily_returns.append(0.0)
            initial_capital_state = self.current_capital

        return self.calculate_metrics()

    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Computes CAGR, Max Drawdown, Win Rate based on trade_log.
        """
        if not self.trade_log:
            return {"status": "No Trades"}

        df_trades = pd.DataFrame(self.trade_log)
        total_pnl = self.current_capital - self.capital
        roi_pct = (total_pnl / self.capital) * 100

        # Win Rate
        wins = df_trades[df_trades['pnl'] > 0]
        win_rate = len(wins) / len(df_trades) if len(df_trades) > 0 else 0.0

        # Max Drawdown
        capital_series = df_trades['capital_after']
        peak = capital_series.cummax()
        drawdown = (capital_series - peak) / peak
        max_drawdown = drawdown.min() * 100

        return {
            "total_trades": len(df_trades),
            "final_capital": round(self.current_capital, 2),
            "total_return_pct": round(roi_pct, 2),
            "win_rate_pct": round(win_rate * 100, 1),
            "max_drawdown_pct": round(max_drawdown, 2)
        }
