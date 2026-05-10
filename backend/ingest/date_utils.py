"""Date utilities - Based on nselib v2.4.3 and User Requirements"""
from datetime import datetime, date, timedelta
from typing import Optional, Set
import pandas as pd
import logging
from backend.config.defaults.nse import DEFAULT_NSE_HOLIDAYS

logger = logging.getLogger(__name__)

class NSEHolidayCalendar:
    """NSE holiday calendar"""

    HOLIDAYS: Set[str] = DEFAULT_NSE_HOLIDAYS

    @classmethod
    def is_trading_day(cls, dt: date) -> bool:
        """Check if date is a trading day"""
        # Weekend check
        if dt.weekday() >= 5:  # 5=Sat, 6=Sun
            return False
        # Holiday check
        return dt.strftime("%Y-%m-%d") not in cls.HOLIDAYS

    @classmethod
    def get_previous_trading_day(cls, dt: date) -> date:
        """Get previous trading day"""
        prev = dt - timedelta(days=1)
        while not cls.is_trading_day(prev):
            prev -= timedelta(days=1)
        return prev

    @classmethod
    def get_next_trading_day(cls, dt: date) -> date:
        """Get next trading day"""
        next_day = dt + timedelta(days=1)
        while not cls.is_trading_day(next_day):
            next_day += timedelta(days=1)
        return next_day

def format_nse_date(dt: date, format_str: str) -> str:
    """Format date for NSE URLs"""
    try:
        # Some NSE URLs use uppercase Month (e.g. 06FEB2026)
        if "%b" in format_str and format_str.replace("%b", "").isalnum():
             # Heuristic: if format is like %d%b%Y, often NSE wants uppercase JAN/FEB
             formatted = dt.strftime(format_str)
             # If strictly alphanumeric (no separators like -), likely needs upper
             if "-" not in format_str:
                 return formatted.upper()
             return formatted
        return dt.strftime(format_str)
    except Exception as e:
        logger.error(f"Date formatting error: {e}")
        return dt.strftime("%d%m%Y")

def parse_nse_datetime(date_str: str) -> Optional[datetime]:
    """Parse NSE datetime strings"""
    if pd.isna(date_str) or not date_str or str(date_str).strip().lower() == "nan":
        return None
    date_str = str(date_str).strip()
    if date_str in ["", "-"]:
        return None

    formats = [
        "%d-%b-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Try just parsing the date and defaulting time
    d = parse_nse_date(date_str)
    if d:
        return datetime.combine(d, datetime.min.time())
    return None

def parse_nse_date(date_str: str) -> Optional[date]:
    """Parse NSE dates - handles multiple formats"""
    if pd.isna(date_str) or not date_str or str(date_str).strip().lower() == "nan":
        return None

    date_str = str(date_str).strip()
    if date_str in ["", "-"]:
        return None

    # Try all possible NSE formats
    formats = [
        "%d-%m-%Y",      # 23-02-2026
        "%d-%b-%Y",      # 23-Feb-2026
        "%d-%b-%y",      # 23-Feb-26
        "%Y-%m-%d",      # 2026-02-23
        "%d%m%Y",        # 23022026
        "%d%b%Y",        # 23Feb2026
        "%d-%B-%Y",      # 23-February-2026
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    # Try with uppercase for month
    for fmt in formats:
        try:
             # This handles cases where %b expects "Feb" but string is "FEB"
             # actually strptime is case-insensitive for %b in many locales, but let's be safe?
             # Python's strptime is locale dependent.
             pass
        except:
            pass

    # Special handling for "06-FEB-2026" if standard failed
    try:
        return datetime.strptime(date_str.title(), "%d-%b-%Y").date()
    except:
        pass

    # Pandas fallback (very robust)
    try:
        ts = pd.to_datetime(date_str, dayfirst=True)
        if not pd.isna(ts):
            return ts.date()
    except:
        pass

    logger.warning(f"Could not parse date: {date_str}")
    return None
