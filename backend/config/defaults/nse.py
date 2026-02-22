"""NSE Importer Configuration"""
from datetime import timedelta

# URLs (NO trailing spaces!)
NSE_ARCHIVES_BASE = "https://nsearchives.nseindia.com"
NSE_MAIN_URL = "https://www.nseindia.com"

# Request Settings
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 1
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# File Patterns: (url_pattern, date_format, handler_key)
NSE_FILE_PATTERNS = {
    "sec_bhavdata": ("/products/content/sec_bhavdata_full_{date}.csv", "ddmmyyyy", "bhavcopy_eq"),
    "fno_bhav": ("/content/fo/BhavCopy_NSE_FO_0_0_0_{date}_F_0000.csv.zip", "yyyymmdd", "bhavcopy_fo"),
    "block_deals": ("/reports/block_deals_{date}.csv", "ddmmyyyy", "block_deals"),
    "bulk_deals": ("/reports/bulk_deals_{date}.csv", "ddmmyyyy", "bulk_deals"),
    "fao_participant_oi": ("/reports/fao_participant_oi_{date}.csv", "ddmmyy", "fao_participant_oi"),
    "fii_stats": ("/reports/fii_stats_{date}.xls", "dd-MMM-yyyy", "fii_derivatives_stats"),
    "fovolt": ("/reports/FOVOLT_{date}.csv", "ddmmyy", "fo_volatility"),
    "mto": ("/reports/MTO_{date}.DAT", "ddmmyyyy", "mto_delivery"),
    "mwpl_cli": ("/reports/mwpl_cli_{date}.xls", "ddmmyyyy", "mwpl_client_position"),
    "nse_security": ("/content/cm/BhavCopy_NSE_CM_0_0_0_{date}_F_0000.csv.gz", "yyyymmdd", "security_master"),
    "pe_ratio": ("/reports/PE_{date}.csv", "ddmmyy", "pe_ratio"),
}

# 2026 NSE Holidays (update annually)
DEFAULT_NSE_HOLIDAYS = {
    "2026-01-15", "2026-01-26", "2026-03-26", "2026-03-31",
    "2026-04-03", "2026-04-14", "2026-05-01", "2026-05-28",
    "2026-06-26", "2026-09-14", "2026-10-02", "2026-10-20",
    "2026-11-08", "2026-11-10", "2026-11-24", "2026-12-25",
}

# TimescaleDB Retention Policies (days)
TIMESCALE_RETENTION = {
    "bhavcopy_eq": 365,
    "bhavcopy_fo": 365,
    "block_deals": 730,
    "bulk_deals": 730,
    "fao_participant_oi": 365,
    "fii_derivatives_stats": 365,
    "fo_volatility": 365,
    "mto_delivery": 365,
    "mwpl_client_position": 365,
    "pe_ratio": 365,
    "security_master": None,  # Keep forever
}

# Compression Policy (compress data older than X days)
TIMESCALE_COMPRESSION_AFTER_DAYS = 30
