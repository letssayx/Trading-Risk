"""NSE Configuration - Based on nselib v2.4.3 and User Requirements"""
from typing import Dict, Tuple, List, Union

# Base URLs
NSE_BASE_URL = "https://www.nseindia.com"
NSE_ARCHIVES_BASE = "https://nsearchives.nseindia.com"

# DEPRECATED: Patterns are now handled in backend/ingest/nse_lib.py
# Kept temporarily for backward compatibility with older code/tests.
NSE_FILE_PATTERNS: Dict[str, Tuple[List[Tuple[str, str]], str]] = {
    "bhavcopy_eq": ([
        ("/products/content/sec_bhavdata_full_{}.csv", "%d%m%Y"),
    ], "bhavcopy_eq"),
}

# HTTP Headers - Aligned with nselib v2.4.3
REQUEST_HEADERS = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Sec-Fetch-User": "?1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8"
}

# Settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 0.5
RETRY_BACKOFF_FACTOR = 0.5
USER_AGENT = REQUEST_HEADERS['User-Agent']
NSE_MAIN_URL = NSE_BASE_URL

# Holidays
DEFAULT_NSE_HOLIDAYS = {
    '2026-01-15', '2026-01-26', '2026-03-26', '2026-03-31',
    '2026-04-03', '2026-04-14', '2026-05-01', '2026-05-28',
    '2026-06-26', '2026-09-14', '2026-10-02', '2026-10-20',
    '2026-11-08', '2026-11-10', '2026-11-24', '2026-12-25',
}

# TimescaleDB Settings
TIMESCALE_RETENTION = {
    "bhavcopy_eq": 365 * 3,  # 3 years
    "bhavcopy_fo": 365 * 2,   # 2 years
    "fao_participant_oi": 365 * 2,
    "fo_volatility": 365 * 3,
    "fii_derivatives_stats": 365 * 2,
    "bulk_deals": 365 * 3,
    "block_deals": 365 * 3,
    "mto_delivery": 365 * 2,
    "mwpl_client_position": 365,
    "pe_ratio": 365 * 2,
}

TIMESCALE_COMPRESSION_AFTER_DAYS = 7
