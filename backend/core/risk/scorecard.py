class StrategyScorecard:
    """
    Compares Live Results vs Backtest Expectations.
    """
    def __init__(self, historical_win_rate: float):
        self.historical_win_rate = historical_win_rate

    def evaluate(self, closed_trades: list) -> dict:
        if not closed_trades: return {"status": "No Trades"}

        wins = sum(1 for t in closed_trades if t['pnl'] > 0)
        total = len(closed_trades)
        realized_win_rate = (wins / total) * 100

        decay_flag = self.check_decay(realized_win_rate)

        return {
            "realized_win_rate": realized_win_rate,
            "historical_target": self.historical_win_rate,
            "deviation": realized_win_rate - self.historical_win_rate,
            "decay_alert": decay_flag
        }

    def check_decay(self, realized_rate: float) -> bool:
        # Flag if drop > 20% relative to mean
        threshold = self.historical_win_rate * 0.8
        return realized_rate < threshold
