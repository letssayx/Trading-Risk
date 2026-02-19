from datetime import date, timedelta
import calendar

class ContractManager:
    """
    Manages generation of derivative contract symbols (Futures & Options).
    """

    MONTH_CODES = {
        1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN",
        7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
    }

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

            # Find last Thursday
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
