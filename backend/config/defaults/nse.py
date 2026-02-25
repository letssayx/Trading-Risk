"""NSE Configuration - Based on nselib v2.4.3 and User Requirements"""
from typing import Dict, Tuple, List, Union

# Base URLs (Trailing spaces removed as per user report)
NSE_BASE_URL = "https://www.nseindia.com"
NSE_ARCHIVES_BASE = "https://nsearchives.nseindia.com"

# Type alias for file patterns: (List of (URL Pattern, Date Format), Table Name)
# We support multiple potential URL patterns for fallback.
NSE_FILE_PATTERNS: Dict[str, Tuple[List[Tuple[str, str]], str]] = {
    "sec_bhavdata": ([
        ("/products/content/sec_bhavdata_full_{}.csv", "%d%m%Y"),
        ("/archives/equities/bhavcopy/pr/PR{}.zip", "%d%m%y") # Old PR zip fallback
    ], "bhavcopy_eq"),

    "fno_bhav": ([
        ("/content/fo/BhavCopy_NSE_FO_0_0_0_{}_F_0000.csv.zip", "%Y%m%d"),
        ("/archives/fo/bhavcopy/fo{}.zip", "%d%b%Y")
    ], "bhavcopy_fo"),

    "fao_participant_oi": ([
        ("/content/nsccl/fao_participant_oi_{}.csv", "%d%m%Y"), # Primary
        ("/reports/fao_participant_oi_{}.csv", "%d%m%y"),       # Report path
        ("/archives/nsccl/content/fao_participant_oi_{}.csv", "%d%m%Y") # Archive
    ], "fao_participant_oi"),

    "fovolt": ([
        ("/archives/nsccl/volt/FOVOLT_{}.csv", "%d%m%Y"),
        ("/reports/FOVOLT_{}.csv", "%d%m%y")
    ], "fo_volatility"),

    "fii_stats": ([
        ("/content/fo/fii_stats_{}.xls", "%d-%b-%Y"),
        ("/reports/fii_stats_{}.xls", "%d-%b-%Y")
    ], "fii_derivatives_stats"),

    "bulk_deals": ([
        ("/archives/equities/mto/bulk_deals_{}.csv", "%d%m%Y"), # Correct archive path
        ("/reports/bulk_deals_{}.csv", "%d%m%Y")                # Report path
    ], "bulk_deals"),

    "block_deals": ([
        ("/archives/equities/mto/block_deals_{}.csv", "%d%m%Y"), # Correct archive path
        ("/reports/block_deals_{}.csv", "%d%m%Y")                # Report path
    ], "block_deals"),

    "mto": ([
        ("/archives/equities/mto/MTO_{}.DAT", "%d%m%Y"), # Correct archive path
        ("/reports/MTO_{}.DAT", "%d%m%Y")
    ], "mto_delivery"),

    "mwpl_cli": ([
        ("/archives/equities/mto/mwpl_cli_{}.xls", "%d%m%Y"), # Correct archive path
        ("/reports/mwpl_cli_{}.xls", "%d%m%Y")
    ], "mwpl_client_position"),

    "nse_security": ([
        ("/content/cm/BhavCopy_NSE_CM_0_0_0_{}_F_0000.csv.gz", "%d%m%Y"),
        ("/archives/common/NSE_CM_security_{}.csv.gz", "%d%m%Y")
    ], "security_master"),

    "pe_ratio": ([
        ("/products/content/PE_{}.csv", "%d%m%y"),
        ("/reports/PE{}.csv", "%d%m%y")
    ], "pe_ratio"),

    "fii_dii_activity": ([
        ("/reports/fii_dii_activity_{}.xls", "%d%b%Y"),
    ], "fii_dii_activity"),

    "var_begin": ([
        ("/archives/nsccl/var/C_VAR1_{}_1.DAT", "%d%m%Y"),
    ], "var_stats"),

    "var_end": ([
        ("/archives/nsccl/var/C_VAR1_{}_6.DAT", "%d%m%Y"),
    ], "var_stats"),

    "contract_delta": ([
        ("/archives/nsccl/content/Contract_Delta_{}.csv", "%d%m%Y"),
    ], "contract_delta"),

    "margin_trading": ([
        ("/archives/equities/mto/mrg_trading_{}.zip", "%d%m%y"),
    ], "margin_trading"),
}

# HTTP Headers
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
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
