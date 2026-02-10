from typing import List, Dict, Any, Type, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.domain.portfolio.models import TradeSide

class TransactionCostModel:
    def __init__(self, slippage_bps: float = 5.0, stt_pct: float = 0.1, comm_per_lot: float = 20.0):
        self.slippage_bps = slippage_bps # Basis points (0.01%)
        self.stt_pct = stt_pct # Securities Transaction Tax (Equity Delivery 0.1%, F&O 0.01% etc.)
        self.comm_per_lot = comm_per_lot # Commission per lot/order

    def calculate_cost(self, price: float, qty: int, is_buy: bool) -> float:
        notional = price * abs(qty)

        # Slippage: Buy higher, Sell lower
        slippage = notional * (self.slippage_bps / 10000.0)

        # STT (Simplified)
        stt = notional * (self.stt_pct / 100.0)

        # Commission (Flat per order for simplicity, or per lot)
        # Assuming qty is units, need lot size? Or just flat.
        # Let's assume comm_per_lot applies per 'trade' execution here.
        comm = self.comm_per_lot

        return slippage + stt + comm

class BacktestEngine:
    def __init__(self, db: Session):
        self.db = db
        self.trades_buffer: List[Dict] = []
        self.cost_model = TransactionCostModel() # Default

    def run_strategy(self, strategy_cls: Type, config: Dict, start_date: datetime, end_date: datetime, tickers: List[str]):
        """
        Executes a backtest for the given strategy over the date range.
        """
        self.trades_buffer = []
        current_date = start_date

        # Instantiate strategy
        strategy = strategy_cls(config)

        print(f"Starting backtest for {strategy.__class__.__name__} from {start_date} to {end_date}")

        while current_date <= end_date:
            # 1. Fetch Market Snapshot (Mock or DB)
            snapshot = self._fetch_snapshot(current_date, tickers)

            if snapshot:
                # 2. Run Strategy Logic
                try:
                    signals = strategy.run(snapshot) # Assuming interface exists
                except Exception as e:
                    # In production log this, for now pass
                    signals = []

                # 3. Process Signals
                for signal in signals:
                    self._execute_virtual_trade(signal, current_date, snapshot)

            current_date += timedelta(days=1)

        return self.evaluate_performance()

    def _fetch_snapshot(self, date: datetime, tickers: List[str]) -> Dict:
        # Placeholder: Fetch OHLCV from DB for these tickers on this date
        return {
            "timestamp": date,
            "prices": {t: 100.0 + (date.day % 10) for t in tickers}, # Mock price
            "tickers": tickers
        }

    def _execute_virtual_trade(self, signal: Any, date: datetime, snapshot: Dict):
        # Signal: ticker, side, qty
        price = snapshot["prices"].get(signal.ticker, 0.0)
        if price <= 0: return

        qty = signal.qty
        is_buy = signal.side == "BUY"

        # Calculate Costs
        cost = self.cost_model.calculate_cost(price, qty, is_buy)

        # Adjust Execution Price for PnL tracking (Net Price)
        # Buy: Pay Price + Cost/Qty
        # Sell: Receive Price - Cost/Qty
        cost_per_unit = cost / abs(qty) if qty != 0 else 0
        net_price = price + cost_per_unit if is_buy else price - cost_per_unit

        trade = {
            "timestamp": date,
            "ticker": signal.ticker,
            "side": signal.side, # "BUY" or "SELL"
            "qty": qty,
            "gross_price": price,
            "net_price": net_price,
            "transaction_cost": cost,
            "strategy_tag": "Backtest_Run",
            "status": "OPEN",
            "meta_data": {"backtest_run_id": "temp_123"}
        }
        self.trades_buffer.append(trade)

    def evaluate_performance(self):
        total_pnl = 0.0
        total_cost = 0.0

        # Simple FIFO PnL Logic on buffer
        # This is a stub: assuming trades are opened and we mark to market at end?
        # Or simplistic: Sum(Sell Net Price * Qty) - Sum(Buy Net Price * Qty)

        # Let's calculate realized PnL for closed pairs + Unrealized for open
        # For simplicity in this engine update: Total Net Value Change

        for trade in self.trades_buffer:
            total_cost += trade["transaction_cost"]
            # PnL accumulation logic would go here

        return {
            "total_trades": len(self.trades_buffer),
            "total_transaction_costs": total_cost,
            "trades": self.trades_buffer
        }
