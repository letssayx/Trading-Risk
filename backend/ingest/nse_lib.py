"""NSE Library Adapter - Re-implementation of nselib logic"""
import requests
import pandas as pd
import io
import zipfile
import logging
import time
from datetime import date
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class NSELib:
    """
    A robust adapter for fetching NSE data, modeled after the 'nselib' library.
    Handles session management, headers, and specific URL patterns/parsing for each report type.
    """

    BASE_URL = "https://www.nseindia.com"
    ARCHIVES_URL = "https://nsearchives.nseindia.com"

    HEADERS = {
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Sec-Fetch-User": "?1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8"
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._cookies_primed = False

    def _ensure_session(self):
        """Prime cookies if not already done."""
        if self._cookies_primed:
            return

        try:
            logger.info(f"Priming NSE session via {self.BASE_URL}...")
            # Minimal headers for initial handshake often helps
            headers = {
                'User-Agent': self.HEADERS['User-Agent'],
                'Accept': '*/*',
                'Connection': 'keep-alive'
            }
            resp = self.session.get(self.BASE_URL, headers=headers, timeout=10)
            if resp.status_code == 200:
                self._cookies_primed = True
                logger.info("Session primed successfully.")
            else:
                logger.warning(f"Session prime failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"Session prime error: {e}")

    def get(self, url: str) -> requests.Response:
        """Execute GET request with session handling."""
        self._ensure_session()

        # Ensure Referer is set for API calls
        if 'api' in url and 'Referer' not in self.session.headers:
            self.session.headers['Referer'] = self.BASE_URL

        logger.info(f"Fetching {url} ...")
        start_time = time.time()
        try:
            resp = self.session.get(url, timeout=30)
            elapsed = time.time() - start_time
            logger.info(f"Response: {resp.status_code} [{elapsed:.2f}s]")

            # Retry on 401/403 once
            if resp.status_code in (401, 403):
                logger.warning(f"Got {resp.status_code}, re-priming session...")
                self._cookies_primed = False
                self.session.cookies.clear()
                self._ensure_session()
                resp = self.session.get(url, timeout=30)
                logger.info(f"Retry Response: {resp.status_code}")

            return resp
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    def _read_csv(self, content: bytes, **kwargs) -> pd.DataFrame:
        """Helper to read CSV with debug logging of first few lines."""
        try:
            # Decode to string to log preview
            text = content.decode('utf-8', errors='ignore')
            lines = text.split('\n')
            preview = '\n'.join(lines[:5])
            logger.info(f"File Preview (First 5 lines):\n{preview}")

            return pd.read_csv(io.StringIO(text), **kwargs)
        except Exception as e:
            logger.error(f"Error reading CSV content: {e}")
            return pd.DataFrame()

    def get_bhavcopy_eq(self, trade_date: date) -> pd.DataFrame:
        """Get CM Bhavcopy (Equity) - Uses sec_bhavdata_full for delivery info."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/products/content/sec_bhavdata_full_{date_str}.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            df = self._read_csv(resp.content, low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        return pd.DataFrame()

    def get_bhavcopy_fo(self, trade_date: date) -> pd.DataFrame:
        """Get FO Bhavcopy."""
        date_str = trade_date.strftime("%Y%m%d")
        url = f"{self.ARCHIVES_URL}/content/fo/BhavCopy_NSE_FO_0_0_0_{date_str}_F_0000.csv.zip"

        resp = self.get(url)
        if resp.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                csv_name = [n for n in zf.namelist() if n.lower().endswith('.csv')][0]
                with zf.open(csv_name) as f:
                    content = f.read()
                    df = self._read_csv(content, low_memory=False)
                    df.columns = [c.strip() for c in df.columns]
                    return df
        return pd.DataFrame()

    def get_bulk_deals(self, trade_date: date) -> pd.DataFrame:
        """Get Bulk Deals. Try Archive first, then Current."""
        # Note: Archive URL pattern is tricky, often not available publicly for older dates easily via static link
        # But we try the most common pattern found in other scripts
        date_str_dmy = trade_date.strftime("%d-%m-%Y")

        # Try API first as it's more reliable for historical ranges
        url_api = f"{self.BASE_URL}/api/historicalOR/bulk-block-short-deals?optionType=bulk_deals&from={date_str_dmy}&to={date_str_dmy}&csv=true"
        resp = self.get(url_api)
        if resp.status_code == 200:
            df = self._read_csv(resp.content, low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df

        # Fallback to static file (usually only current day)
        if trade_date == date.today():
             url_static = f"{self.ARCHIVES_URL}/content/equities/bulk.csv"
             resp = self.get(url_static)
             if resp.status_code == 200:
                 df = self._read_csv(resp.content, low_memory=False)
                 df.columns = [c.strip() for c in df.columns]
                 return df

        return pd.DataFrame()

    def get_block_deals(self, trade_date: date) -> pd.DataFrame:
        """Get Block Deals."""
        date_str_dmy = trade_date.strftime("%d-%m-%Y")

        url_api = f"{self.BASE_URL}/api/historicalOR/bulk-block-short-deals?optionType=block_deals&from={date_str_dmy}&to={date_str_dmy}&csv=true"
        resp = self.get(url_api)
        if resp.status_code == 200:
            df = self._read_csv(resp.content, low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df

        if trade_date == date.today():
             url_static = f"{self.ARCHIVES_URL}/content/equities/block.csv"
             resp = self.get(url_static)
             if resp.status_code == 200:
                 df = self._read_csv(resp.content, low_memory=False)
                 df.columns = [c.strip() for c in df.columns]
                 return df

        return pd.DataFrame()

    def get_fao_participant_oi(self, trade_date: date) -> pd.DataFrame:
        """Get Participant OI."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/content/nsccl/fao_participant_oi_{date_str}.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            # Skip metadata row if present
            content = resp.content.decode('utf-8', errors='ignore')
            lines = content.split('\n')

            # Log preview
            logger.info(f"File Preview (First 5 lines):\n" + '\n'.join(lines[:5]))

            skiprows = 0
            if len(lines) > 0 and "Participant wise Open Interest" in lines[0]:
                skiprows = 1

            df = pd.read_csv(io.StringIO(content), skiprows=skiprows, low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        return pd.DataFrame()

    def get_fii_derivatives_stats(self, trade_date: date) -> pd.DataFrame:
        """Get FII Stats (Excel)."""
        date_str = trade_date.strftime("%d-%b-%Y")
        url = f"{self.ARCHIVES_URL}/content/fo/fii_stats_{date_str}.xls"

        resp = self.get(url)
        if resp.status_code == 200:
            try:
                # Log that we got content (Excel binary, can't preview text easily)
                logger.info(f"Received Excel file ({len(resp.content)} bytes)")
                df = pd.read_excel(io.BytesIO(resp.content))
                return df
            except Exception as e:
                logger.error(f"FII Stats parse error: {e}")
        return pd.DataFrame()

    def get_fo_volatility(self, trade_date: date) -> pd.DataFrame:
        """Get FO Volatility."""
        date_str = trade_date.strftime("%d%m%Y")
        # Archives path confirmed in nselib
        url = f"{self.ARCHIVES_URL}/archives/nsccl/volt/FOVOLT_{date_str}.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            df = self._read_csv(resp.content, low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        return pd.DataFrame()

    def get_mto_delivery(self, trade_date: date) -> pd.DataFrame:
        """Get MTO Delivery Data (.DAT)."""
        date_str = trade_date.strftime("%d%m%Y")
        # Try both common paths
        urls = [
            f"{self.ARCHIVES_URL}/archives/equities/mto/MTO_{date_str}.DAT",
            f"{self.ARCHIVES_URL}/content/equities/MTO_{date_str}.DAT"
        ]

        for url in urls:
            resp = self.get(url)
            if resp.status_code == 200:
                content = resp.content.decode('utf-8', errors='ignore')
                lines = content.strip().split('\n')

                # Log preview
                logger.info(f"File Preview (First 5 lines):\n" + '\n'.join(lines[:5]))

                # Robust logic: Find header line starting with "Record Type" or "20" (data)
                header_idx = -1
                for i, line in enumerate(lines[:20]):
                    if "Record Type" in line and "Name of Security" in line:
                        header_idx = i
                        break

                if header_idx != -1 and len(lines) > header_idx + 1:
                    header = lines[header_idx]
                    data = lines[header_idx+1:]
                    csv_str = header + '\n' + '\n'.join(data)
                    df = pd.read_csv(io.StringIO(csv_str), low_memory=False)
                    df.columns = [c.strip() for c in df.columns]
                    return df
                else:
                    # Fallback: sometimes no header, just data?
                    # If it looks like CSV (commas), try reading directly
                    if ',' in lines[0]:
                         # Assuming standard columns: Record Type, Sr No, Name of Security, Quantity Traded, Deliverable Quantity, % Deliverable
                         # But risky. Let's return empty if we can't find header.
                         pass
                break # Stop if found

        return pd.DataFrame()

    def get_mwpl(self, trade_date: date) -> pd.DataFrame:
        """Get MWPL Data (Excel)."""
        date_str = trade_date.strftime("%d%m%Y")
        # Try known paths
        urls = [
            f"{self.ARCHIVES_URL}/content/nsccl/mwpl_cli_{date_str}.xls",
            f"{self.ARCHIVES_URL}/archives/equities/mto/mwpl_cli_{date_str}.xls"
        ]

        for url in urls:
            resp = self.get(url)
            if resp.status_code == 200:
                try:
                    logger.info(f"Received Excel file ({len(resp.content)} bytes)")
                    # Read full excel
                    df = pd.read_excel(io.BytesIO(resp.content), header=None)

                    # Scan for header row
                    header_row_idx = -1
                    for i, row in df.iterrows():
                        row_vals = [str(x).strip() for x in row.values if pd.notna(x)]
                        if 'Underlying Stock' in row_vals and 'Client 1' in row_vals:
                            header_row_idx = i
                            break

                    if header_row_idx != -1:
                        # Reload with correct header
                        df.columns = df.iloc[header_row_idx]
                        df = df.iloc[header_row_idx+1:].reset_index(drop=True)
                        return df
                except Exception as e:
                     logger.error(f"MWPL parse error: {e}")
                break

        return pd.DataFrame()

    def get_pe_ratio(self, trade_date: date) -> pd.DataFrame:
        """Get P/E Ratio."""
        # Try multiple date formats as NSE is inconsistent
        formats = ["%d%m%Y", "%d-%b-%Y"]

        for fmt in formats:
            date_str = trade_date.strftime(fmt)
            if "%b" in fmt: date_str = date_str.upper() # 24-FEB-2026 ??

            # Paths to try
            urls = [
                f"{self.ARCHIVES_URL}/products/content/equities/pe/pe_ind_{date_str}.csv", # Official product path
                f"{self.ARCHIVES_URL}/content/equities/pe/peind_{date_str}.csv"
            ]

            for url in urls:
                resp = self.get(url)
                if resp.status_code == 200:
                    df = self._read_csv(resp.content, low_memory=False)
                    df.columns = [c.strip() for c in df.columns]
                    return df

        return pd.DataFrame()

    def get_security_master(self, trade_date: date) -> pd.DataFrame:
        """Get Security Master (EQUITY_L.csv)."""
        # This is usually a static file updated daily, not archived by date easily via public link?
        # But we can try the static link
        url = f"{self.ARCHIVES_URL}/content/equities/EQUITY_L.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            df = self._read_csv(resp.content, low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        return pd.DataFrame()
