from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Tuple
from datetime import date, timedelta
from backend.domain.market.models import Bhavcopy

class ContractManager:
    """
    Manages logic for Futures Expiry Rolling (FUT1/2/3) and Options Chain Selection.
    """

    @staticmethod
    def get_futures_chain(db: Session, symbol: str, trade_date: date) -> List[Bhavcopy]:
        """
        Returns Futures contracts for a symbol on a given date, sorted by expiry.
        Limit to 3 (Near, Next, Far).
        """
        # Fetch futures for this symbol and date
        # Instrument type: FUTSTK or FUTIDX
        futures = db.query(Bhavcopy).filter(
            Bhavcopy.symbol == symbol,
            Bhavcopy.trade_date == trade_date,
            Bhavcopy.instrument_type.in_(['FUTSTK', 'FUTIDX'])
        ).order_by(Bhavcopy.expiry_date.asc()).limit(3).all()

        return futures

    @staticmethod
    def get_specific_future(db: Session, symbol: str, trade_date: date, position: int = 1) -> Optional[Bhavcopy]:
        """
        Get specific future contract (1=Near, 2=Next, 3=Far)
        """
        chain = ContractManager.get_futures_chain(db, symbol, trade_date)
        if len(chain) >= position:
            return chain[position - 1]
        return None

    @staticmethod
    def get_continuous_future(db: Session, symbol: str, position: int = 1, start_date: date = None, end_date: date = None) -> List[dict]:
        """
        Constructs a continuous price series by stitching contracts.
        Simplistic approach: For each day in range, pick the 'position-th' nearest expiry.
        """
        if not start_date: start_date = date.today() - timedelta(days=365)
        if not end_date: end_date = date.today()

        # Get all distinct trade dates
        dates = db.query(Bhavcopy.trade_date).filter(
            Bhavcopy.symbol == symbol,
            Bhavcopy.trade_date >= start_date,
            Bhavcopy.trade_date <= end_date
        ).distinct().order_by(Bhavcopy.trade_date.asc()).all()

        result = []
        for (d,) in dates:
            contract = ContractManager.get_specific_future(db, symbol, d, position)
            if contract:
                result.append({
                    "date": d,
                    "contract_symbol": contract.symbol, # Include mapped symbol (e.g., RELIANCE26FEB...)
                    "expiry": contract.expiry_date,
                    "open": contract.open,
                    "high": contract.high,
                    "low": contract.low,
                    "close": contract.close,
                    "volume": contract.total_traded_qty,
                    "oi": contract.open_interest
                })
        return result
