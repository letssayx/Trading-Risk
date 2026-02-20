from datetime import date, timedelta
import calendar
from typing import Optional, Tuple

class ContractManager:
    """
    Manages generation of derivative contract symbols (Futures & Options).
    """

    MONTH_CODES = {
        1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN",
        7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
    }

    # Reverse mapping for parsing
    MONTH_CODES_REV = {v: k for k, v in MONTH_CODES.items()}

    @staticmethod
    def get_expiry_dates(limit=3):
        """
        Get the next `limit` expiry dates (Last Thursday of the month).
        If last Thursday is a holiday, it should ideally be the previous trading day,
        but for symbol generation, standard practice is often just the month/year code
        or the specific date depending on the exchange format.
        NSE format: SYMBOL + YY + MMM + FUT
        """
        expiries = []
        today = date.today()
        current_date = today

        # Simple logic: Find last Thursday of current month, if passed, move to next.
        # However, for symbol generation, we often just need the Month and Year.
        # NSE Symbol: RELIANCE24FEBFUT

        for _ in range(limit):
            # Find last day of current_date's month
            last_day = calendar.monthrange(current_date.year, current_date.month)[1]
            last_date_of_month = date(current_date.year, current_date.month, last_day)

            # Find last Thursday (weekday 3)
            # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
            # Wait, original code had `(last_date_of_month.weekday() - 1) % 7` for Tuesday??
            # NSE Expiry is Thursday. Let's fix to Thursday (3).
            offset = (last_date_of_month.weekday() - 3) % 7
            expiry_date = last_date_of_month - timedelta(days=offset)

            if expiry_date < today and len(expiries) == 0:
                # If this month's expiry is already passed, skip to next month
                pass
            else:
                expiries.append(expiry_date)

            # Move to next month
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)

            if len(expiries) >= limit:
                break

        return expiries

    @staticmethod
    def get_futures_symbols(symbol: str):
        """
        Generate Futures symbols for the given underlying symbol.
        Format: SYMBOL + YY + MMM + FUT (e.g. RELIANCE24FEBFUT)
        """
        expiries = ContractManager.get_expiry_dates(3)
        futures = []

        for expiry in expiries:
            yy = str(expiry.year)[-2:]
            mmm = ContractManager.MONTH_CODES[expiry.month]
            fut_symbol = f"{symbol}{yy}{mmm}FUT"
            futures.append(fut_symbol)

        return futures

    @staticmethod
    def parse_contract_symbol(contract_symbol: str) -> Optional[Tuple[str, int, int]]:
        """
        Parses a contract symbol like RELIANCE24FEBFUT into (Symbol, Year, Month).
        Returns None if format is invalid.
        """
        s = contract_symbol.upper()
        if not s.endswith("FUT"):
            return None

        # Format: SYMBOL + YY + MMM + FUT
        # Minimum length: 1 (S) + 2 (YY) + 3 (MMM) + 3 (FUT) = 9
        if len(s) < 9:
            return None

        try:
            yy_str = s[-8:-6]
            mmm_str = s[-6:-3]
            symbol = s[:-8]

            if not yy_str.isdigit():
                return None

            year = 2000 + int(yy_str)
            month = ContractManager.MONTH_CODES_REV.get(mmm_str)

            if not month:
                return None

            return (symbol, year, month)

        except Exception:
            return None
