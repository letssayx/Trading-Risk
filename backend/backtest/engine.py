from typing import List, Dict, Any, Type
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.domain.portfolio.models import TradeSide
# Assuming a BaseStrategy exists or passing class dynamically

class BacktestEngine:
    def __init__(self, db: Session):
        self.db = db
        self.trades_buffer: List[Dict] = []

    def run_strategy(self, strategy_cls: Type, config: Dict, start_date: datetime, end_date: datetime, tickers: List[str]):
        """
        Executes a backtest for the given strategy over the date range.
        """
        self.trades_buffer = []
        current_date = start_date

        # Instantiate strategy
        strategy = strategy_cls(config)

        print(f"Starting backtest for {strategy.name} from {start_date} to {end_date}")

        while current_date <= end_date:
            # 1. Fetch Market Snapshot (Mock or DB)
            # In a real implementation, this queries MarketData/TimescaleDB
            snapshot = self._fetch_snapshot(current_date, tickers)

            if snapshot:
                # 2. Run Strategy Logic
                # strategy.run() should return a list of Signal objects or dicts
                try:
                    signals = strategy.run(snapshot)
                except Exception as e:
                    print(f"Error running strategy on {current_date}: {e}")
                    signals = []

                # 3. Process Signals
                for signal in signals:
                    self._execute_virtual_trade(signal, current_date, snapshot)

            current_date += timedelta(days=1)

        return self.evaluate_performance()

    def _fetch_snapshot(self, date: datetime, tickers: List[str]) -> Dict:
        # Placeholder: Fetch OHLCV from DB for these tickers on this date
        # Returning a mock structure for now
        return {
            "timestamp": date,
            "prices": {t: 100.0 + (date.day % 10) for t in tickers}, # Mock price movement
            "tickers": tickers
        }

    def _execute_virtual_trade(self, signal: Any, date: datetime, snapshot: Dict):
        # Signal expected to have: ticker, side, qty
        price = snapshot["prices"].get(signal.ticker, 0.0)

        trade = {
            "timestamp": date,
            "ticker": signal.ticker,
            "side": signal.side, # "BUY" or "SELL"
            "qty": signal.qty,
            "price": price,
            "strategy_tag": "Backtest_Run",
            "status": "OPEN",
            "meta_data": {"backtest_run_id": "temp_123"}
        }
        self.trades_buffer.append(trade)

    def evaluate_performance(self):
        # Simple PnL calculation assuming closure at end or FIFO
        total_pnl = 0.0
        wins = 0
        losses = 0

        # Very basic logic: Close all positions at last price (not implemented here fully)
        # Just summarizing trades count
        return {
            "total_trades": len(self.trades_buffer),
            "trades": self.trades_buffer
        }
