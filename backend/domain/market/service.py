from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, distinct
from datetime import date, datetime
import pandas as pd
from backend.domain.market.models import Bhavcopy
from backend.domain.market.contract_manager import ContractManager

class MarketDataService:

    @staticmethod
    def get_latest_date(db: Session, segment: str = None) -> Optional[date]:
        """Get the most recent trade date available."""
        query = db.query(func.max(Bhavcopy.trade_date))
        if segment:
            query = query.filter(Bhavcopy.segment == segment)
        return query.scalar()

    @staticmethod
    def get_daily_ohlc(db: Session, symbol: str, days: int = 365, segment: str = 'CM') -> List[Dict[str, Any]]:
        """
        Fetch OHLC data for a symbol.
        """
        target_symbol = symbol
        target_expiry = None
        target_segment = segment

        # Try to parse as contract
        parsed = ContractManager.parse_contract_symbol(symbol)
        matched_date = None

        query = db.query(Bhavcopy).filter(Bhavcopy.symbol == target_symbol)

        if parsed:
            target_symbol = parsed[0]
            target_year = parsed[1]
            target_month_code = ContractManager.MONTH_CODES[parsed[2]]

            # Find distinct expiry dates for this symbol
            expiries = db.query(Bhavcopy.expiry_date).filter(
                Bhavcopy.symbol == target_symbol,
                Bhavcopy.segment == 'FO',
                Bhavcopy.expiry_date != None
            ).distinct().all()

            for exp in expiries:
                d = exp[0]
                if d.year == target_year and ContractManager.MONTH_CODES.get(d.month) == target_month_code:
                    matched_date = d
                    break

            if matched_date:
                query = db.query(Bhavcopy).filter(
                    Bhavcopy.symbol == target_symbol,
                    Bhavcopy.expiry_date == matched_date,
                    Bhavcopy.instrument_type.like('FUT%')
                )
            else:
                return []
        else:
            # Normal CM or Underlying
            if target_segment == 'CM':
                query = query.filter(Bhavcopy.segment == 'CM')
                query = query.filter(Bhavcopy.series.in_(['EQ', 'BE']))

        # Sort and limit
        query = query.order_by(Bhavcopy.trade_date.desc()).limit(days)

        results = query.all()
        results.reverse()

        data = []
        for row in results:
            data.append({
                "time": row.trade_date.strftime("%Y-%m-%d"),
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.total_traded_qty or 0,
                "oi": row.open_interest or 0,
                "expiry": row.expiry_date.strftime("%Y-%m-%d") if row.expiry_date else None,
                "symbol": row.symbol
            })

        return data

    @staticmethod
    def search_symbols(db: Session, query_str: str, segment: str = 'EQ') -> List[str]:
        """
        Search for symbols.
        """
        q = query_str.upper()

        if segment == 'EQ' or segment == 'CM':
            results = db.query(distinct(Bhavcopy.symbol)).filter(
                Bhavcopy.segment == 'CM',
                Bhavcopy.symbol.contains(q)
            ).limit(20).all()
            return [r[0] for r in results]

        elif segment == 'FO' or segment == 'FUT':
            symbols = db.query(distinct(Bhavcopy.symbol)).filter(
                Bhavcopy.segment == 'FO',
                Bhavcopy.symbol.contains(q),
                Bhavcopy.instrument_type.like('FUT%')
            ).limit(10).all()

            contracts = []
            for r in symbols:
                sym = r[0]
                contracts.extend(MarketDataService.get_contracts_for_underlying(db, sym))

            return contracts

        return []

    @staticmethod
    def get_contracts_for_underlying(db: Session, symbol: str) -> List[str]:
        """
        Get valid contract strings for an underlying.
        """
        contracts = []
        expiries = db.query(distinct(Bhavcopy.expiry_date)).filter(
            Bhavcopy.symbol == symbol,
            Bhavcopy.segment == 'FO',
            Bhavcopy.instrument_type.like('FUT%')
        ).order_by(Bhavcopy.expiry_date).all()

        for exp_row in expiries:
            exp = exp_row[0]
            if not exp: continue

            yy = str(exp.year)[-2:]
            mmm = ContractManager.MONTH_CODES.get(exp.month)
            if mmm:
                contract = f"{symbol}{yy}{mmm}FUT"
                contracts.append(contract)
        return contracts

    @staticmethod
    def get_latest_price(db: Session, symbol: str) -> Optional[Dict[str, Any]]:
        """Get the latest close price and date for a symbol."""
        parsed = ContractManager.parse_contract_symbol(symbol)

        if parsed:
            target_symbol = parsed[0]
            target_year = parsed[1]
            target_month_code = ContractManager.MONTH_CODES[parsed[2]]

            candidates = db.query(distinct(Bhavcopy.expiry_date)).filter(
                Bhavcopy.symbol == target_symbol,
                Bhavcopy.segment == 'FO'
            ).all()

            matched_date = None
            for row in candidates:
                d = row[0]
                if d and d.year == target_year and ContractManager.MONTH_CODES.get(d.month) == target_month_code:
                    matched_date = d
                    break

            if not matched_date:
                return None

            record = db.query(Bhavcopy).filter(
                Bhavcopy.symbol == target_symbol,
                Bhavcopy.expiry_date == matched_date,
                Bhavcopy.instrument_type.like('FUT%')
            ).order_by(Bhavcopy.trade_date.desc()).first()

        else:
            record = db.query(Bhavcopy).filter(
                Bhavcopy.symbol == symbol,
                Bhavcopy.segment == 'CM'
            ).order_by(Bhavcopy.trade_date.desc()).first()

        if record:
            return {
                "price": record.close,
                "date": record.trade_date.strftime("%Y-%m-%d"),
                "symbol": record.symbol
            }
        return None

    @staticmethod
    def get_spread_series(db: Session, symbol1: str, symbol2: str, ratio: float = 1.0, days: int = 365) -> List[Dict[str, Any]]:
        """Get aligned spread history."""
        data1 = MarketDataService.get_daily_ohlc(db, symbol1, days=days)
        data2 = MarketDataService.get_daily_ohlc(db, symbol2, days=days)

        if not data1 or not data2:
            return []

        df1 = pd.DataFrame(data1).set_index('time')
        df2 = pd.DataFrame(data2).set_index('time')

        aligned = df1.join(df2, lsuffix='_1', rsuffix='_2', how='inner')

        spread_data = []
        for date_str, row in aligned.iterrows():
            val = row['close_1'] - (ratio * row['close_2'])
            spread_data.append({
                "time": date_str,
                "value": round(val, 2)
            })

        return spread_data
