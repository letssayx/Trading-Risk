import pandas as pd
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from backend.strategies.base_strategy import BaseStrategy

class BacktestEngine:
    """
    Simulates market execution by replaying historical data
    from TimescaleDB against a BaseStrategy instance.
    """
    def __init__(self, db: Session, strategy: BaseStrategy, initial_capital: float = 1000000.0):
        self.db = db
        self.strategy = strategy
        self.capital = initial_capital
        self.current_capital = initial_capital
        self.positions: List[Dict[str, Any]] = []
        self.trade_log: List[Dict[str, Any]] = []

    def run(self, turtle_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Executes the backtest simulation.
        """
        # 1. Fetch historical data from TimescaleDB (Simulated logic if db is mock)
        if self.db:
            query = f"""
                SELECT * FROM market_data
                WHERE turtle_id = '{turtle_id}'
                AND time BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY time ASC
            """
            try:
                # Using bind/connection to read sql
                df = pd.read_sql(query, self.db.bind)
            except Exception:
                # Fallback for testing without DB
                df = pd.DataFrame()
        else:
            df = pd.DataFrame() # Testing mode

        if df.empty:
            return {"status": "No Data found for backtest"}

        # 2. Compute deterministic indicators
        df = self.strategy.compute_indicators(df)

        # 3. Replay loop (The 'Time Machine')
        # Simplified loop: Iterate row by row.
        # For efficiency in production, vectorization is preferred, but loop mimics event-driven.

        for i in range(len(df)):
            # Slice up to current point to avoid lookahead bias if strategy looks back
            # But strategies usually take the full DF and assume row 'i' is 'now'.
            # Optimized strategies just look at row 'i'.
            # BaseStrategy interface takes full DF. Let's assume it handles lookback safely or we pass slice.
            # Passing slice is slow. Better: compute_indicators is done once. check_signals takes full DF but looks at index i.
            # But check_signals signature is `(df, pos)`.
            # To simulate "live", we pass `df.iloc[:i+1]`.

            current_slice = df.iloc[:i+1]
            # Current holdings for this ticker? Assuming simple 1-asset backtest for now.
            current_pos = self.positions[0] if self.positions else {}

            signal = self.strategy.check_signals(current_slice, current_pos)
            current_bar = df.iloc[i]

            if signal == 'BUY' and not self.positions:
                self._execute_trade(current_bar, 'BUY')
            elif signal == 'SELL' and self.positions:
                # Check if we are Long. If so, Sell to close.
                # If Short logic exists, it would be different. Assuming Long-Only for simplicity or System 1 logic.
                self._execute_trade(current_bar, 'SELL')
            elif signal == 'EXIT' and self.positions:
                self._execute_trade(current_bar, 'SELL') # Exit is a Sell

        return self._calculate_metrics()

    def _execute_trade(self, bar: pd.Series, side: str):
        # Simple execution logic
        price = bar['close']
        time = bar['time'] if 'time' in bar else bar.name # Handle index if time is index

        if side == 'BUY':
            # Buy logic (All in)
            qty = int(self.current_capital / price)
            cost = qty * price
            self.current_capital -= cost
            self.positions.append({"entry_price": price, "quantity": qty, "entry_time": time})
            self.trade_log.append({"time": time, "side": "BUY", "price": price, "qty": qty})

        elif side == 'SELL':
            # Sell logic (Close all)
            if not self.positions: return
            pos = self.positions.pop(0)
            revenue = pos['quantity'] * price
            self.current_capital += revenue
            pnl = revenue - (pos['quantity'] * pos['entry_price'])

            self.trade_log.append({
                "time": time, "side": "SELL", "price": price,
                "qty": pos['quantity'], "pnl": pnl
            })

    def _calculate_metrics(self) -> Dict[str, Any]:
        """
        Computes CAGR, Max Drawdown, Win Rate based on trade_log.
        """
        if not self.trade_log:
            return {"total_return_pct": 0.0, "trades": 0}

        # PnL Analysis
        closed_trades = [t for t in self.trade_log if "pnl" in t]
        total_pnl = sum(t['pnl'] for t in closed_trades)
        roi_pct = (total_pnl / self.capital) * 100

        wins = [t for t in closed_trades if t['pnl'] > 0]
        win_rate = len(wins) / len(closed_trades) if closed_trades else 0.0

        # Max Drawdown (Simple approximation on closed equity curve)
        # In prod, calculate on daily equity curve.
        equity = self.capital
        peaks = equity
        max_dd = 0

        for t in closed_trades:
            equity += t['pnl']
            if equity > peaks:
                peaks = equity
            dd = (peaks - equity) / peaks
            if dd > max_dd:
                max_dd = dd

        return {
            "total_trades": len(closed_trades),
            "final_capital": round(self.current_capital, 2),
            "total_return_pct": round(roi_pct, 2),
            "win_rate_pct": round(win_rate * 100, 1),
            "max_drawdown_pct": round(max_dd * 100, 2)
        }
