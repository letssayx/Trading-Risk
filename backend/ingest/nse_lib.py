"""NSE Library Adapter - Re-implementation of nselib logic"""
import requests
import pandas as pd
import io
import zipfile
import logging
import os
from datetime import date
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NSELib:
    """
    A robust adapter for fetching NSE data, modeled after the 'nselib' library.
    Handles session management, headers, and specific URL patterns/parsing for each report type.
    Includes fallback to local file reading if network requests fail.
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

    DOWNLOAD_DIR = "backend/downloads" # Directory to check for local files

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

        resp = self.session.get(url, timeout=30)

        # Retry on 401/403 once
        if resp.status_code in (401, 403):
            logger.warning(f"Got {resp.status_code}, re-priming session...")
            self._cookies_primed = False
            self.session.cookies.clear()
            self._ensure_session()
            resp = self.session.get(url, timeout=30)

        return resp

    def _read_local_file(self, filename: str) -> Optional[bytes]:
        """Attempt to read file from local DOWNLOAD_DIR."""
        filepath = os.path.join(os.getcwd(), self.DOWNLOAD_DIR, filename)
        if os.path.exists(filepath):
            logger.info(f"Found local file: {filepath}")
            try:
                with open(filepath, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read local file {filepath}: {e}")
        return None

    def _read_excel_robust(self, content: bytes, header_val=None) -> pd.DataFrame:
        """
        Attempt to read Excel content using multiple engines/strategies.
        Prioritizes auto-detection, then xlrd (for xls), then openpyxl (for xlsx).
        """
        bio = io.BytesIO(content)

        # Strategy 1: Default (Auto-detect)
        try:
            bio.seek(0)
            return pd.read_excel(bio, header=header_val)
        except Exception as e1:
            logger.warning(f"Excel read (auto) failed: {e1}. Retrying with engines...")

        # Strategy 2: xlrd (Explicit for legacy .xls)
        try:
            bio.seek(0)
            return pd.read_excel(bio, header=header_val, engine='xlrd')
        except Exception as e2:
            logger.warning(f"Excel read (xlrd) failed: {e2}")

        # Strategy 3: openpyxl (Explicit for .xlsx)
        try:
            bio.seek(0)
            return pd.read_excel(bio, header=header_val, engine='openpyxl')
        except Exception as e3:
            logger.error(f"Excel read (openpyxl) failed: {e3}")
            raise ValueError(f"Failed to parse Excel file with any engine. Last error: {e3}")

    # --- Public parsing methods ---
    def parse_mwpl(self, content: bytes) -> pd.DataFrame:
        """Parse MWPL Excel content."""
        try:
            # Use header=None to let FieldMapper find the correct header row
            df = self._read_excel_robust(content, header_val=None)
            return df
        except Exception as e:
            logger.error(f"MWPL parse error: {e}")
            return pd.DataFrame()

    def parse_mto(self, content: bytes) -> pd.DataFrame:
        """Parse MTO .DAT content."""
        try:
            decoded_content = content.decode('utf-8', errors='ignore')
            lines = decoded_content.strip().split('\n')

            # Robust logic: Find header line starting with "Record Type"
            header_idx = -1
            for i, line in enumerate(lines[:10]): # Check first 10 lines
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
        except Exception as e:
            logger.error(f"MTO parse error: {e}")
        return pd.DataFrame()

    def parse_fao_participant_oi(self, content: bytes) -> pd.DataFrame:
        """Parse FAO Participant OI CSV content."""
        try:
            # Skip metadata row if present
            decoded_content = content.decode('utf-8', errors='ignore')
            skiprows = 1 if "Participant wise Open Interest" in decoded_content.split('\n')[0] else 0

            df = pd.read_csv(io.StringIO(decoded_content), skiprows=skiprows, low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"FAO Participant OI parse error: {e}")
            return pd.DataFrame()

    def parse_fii_derivatives_stats(self, content: bytes) -> pd.DataFrame:
        """Parse FII Derivatives Stats Excel content."""
        try:
            df = self._read_excel_robust(content)
            return df
        except Exception as e:
            logger.error(f"FII Stats parse error: {e}")
            return pd.DataFrame()

    def get_bhavcopy_eq(self, trade_date: date) -> pd.DataFrame:
        """Get CM Bhavcopy (Equity) - Uses sec_bhavdata_full for delivery info."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/products/content/sec_bhavdata_full_{date_str}.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
            # Clean columns
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
                    df = pd.read_csv(f, low_memory=False)
                    df.columns = [c.strip() for c in df.columns]
                    return df
        return pd.DataFrame()

    def get_bulk_deals(self, trade_date: date) -> pd.DataFrame:
        """Get Bulk Deals via API."""
        # API format: from=dd-mm-yyyy&to=dd-mm-yyyy
        date_str = trade_date.strftime("%d-%m-%Y")
        url = f"{self.BASE_URL}/api/historicalOR/bulk-block-short-deals?optionType=bulk_deals&from={date_str}&to={date_str}&csv=true"

        resp = self.get(url)
        if resp.status_code == 200:
            df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        # Fallback to archives?
        return pd.DataFrame()

    def get_block_deals(self, trade_date: date) -> pd.DataFrame:
        """Get Block Deals via API."""
        date_str = trade_date.strftime("%d-%m-%Y")
        url = f"{self.BASE_URL}/api/historicalOR/bulk-block-short-deals?optionType=block_deals&from={date_str}&to={date_str}&csv=true"

        resp = self.get(url)
        if resp.status_code == 200:
            df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        return pd.DataFrame()

    def get_fao_participant_oi(self, trade_date: date) -> pd.DataFrame:
        """Get Participant OI."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/content/nsccl/fao_participant_oi_{date_str}.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            return self.parse_fao_participant_oi(resp.content)
        return pd.DataFrame()

    def get_fii_derivatives_stats(self, trade_date: date) -> pd.DataFrame:
        """Get FII Stats (Excel)."""
        date_str = trade_date.strftime("%d-%b-%Y")
        url = f"{self.ARCHIVES_URL}/content/fo/fii_stats_{date_str}.xls"

        resp = self.get(url)
        if resp.status_code == 200:
            return self.parse_fii_derivatives_stats(resp.content)
        return pd.DataFrame()

    def get_fo_volatility(self, trade_date: date) -> pd.DataFrame:
        """Get FO Volatility."""
        date_str = trade_date.strftime("%d%m%Y")
        # Try archives first
        url = f"{self.ARCHIVES_URL}/archives/nsccl/volt/FOVOLT_{date_str}.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        return pd.DataFrame()

    def get_mto_delivery(self, trade_date: date) -> pd.DataFrame:
        """Get MTO Delivery Data (.DAT)."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/archives/equities/mto/MTO_{date_str}.DAT"

        resp = self.get(url)
        if resp.status_code == 200:
            return self.parse_mto(resp.content)

        return pd.DataFrame()

    def get_mwpl(self, trade_date: date) -> pd.DataFrame:
        """Get MWPL Data (Excel)."""
        date_str = trade_date.strftime("%d%m%Y")
        base_filename = f"mwpl_cli_{date_str}"
        url = f"{self.ARCHIVES_URL}/archives/equities/mto/{base_filename}.xls"

        # 1. Try local file first (for manual fallback) - Check multiple extensions
        content = None
        for ext in ['.xls', '.xlsx']:
            filename = f"{base_filename}{ext}"
            content = self._read_local_file(filename)
            if content:
                logger.info(f"Using local file: {filename}")
                break

        # 2. Try network if local missing
        if not content:
            resp = self.get(url)
            if resp.status_code == 200:
                content = resp.content
            else:
                # Try .xlsx extension? Rare but possible
                pass

        if content:
            return self.parse_mwpl(content)

        return pd.DataFrame()

    def get_security_master(self, trade_date: date) -> pd.DataFrame:
        """Get Security Master (NSE_CM_security)."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/content/equities/NSE_CM_security_{date_str}.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        return pd.DataFrame()

    def get_pe_ratio(self, trade_date: date) -> pd.DataFrame:
        """Get P/E Ratio Data (Indices)."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/content/indices/ind_close_all_{date_str}.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        return pd.DataFrame()

    def get_margin_trading(self, trade_date: date) -> pd.DataFrame:
        """Get Margin Trading Disclosure."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/archives/equities/mto/margin_{date_str}.zip"

        resp = self.get(url)
        if resp.status_code == 200:
            try:
                with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                    # Usually contains a DAT or CSV file
                    # File name format: MARGIN_TRADING_DISCLOSURE_ddmmyyyy.dat (CSV format)
                    target_file = [n for n in zf.namelist() if 'MARGIN_TRADING' in n][0]
                    with zf.open(target_file) as f:
                        df = pd.read_csv(f, low_memory=False)
                        df.columns = [c.strip() for c in df.columns]
                        return df
            except Exception as e:
                logger.error(f"Error parsing Margin Trading: {e}")
        return pd.DataFrame()

    def get_var_stats(self, trade_date: date, file_type: str = 'BEGIN') -> pd.DataFrame:
        """Get VaR Stats (Begin/End of Day)."""
        # Type: '5' for Begin Day, '6' for End Day (based on typical NSE file naming/structure, but archives differ)
        # Archive URL: https://nsearchives.nseindia.com/archives/nsccl/var/C_VAR1_ddmmyyyy_1.DAT (Begin)
        #              https://nsearchives.nseindia.com/archives/nsccl/var/C_VAR1_ddmmyyyy_6.DAT (End)
        # Using standard robust pattern if possible.

        date_str = trade_date.strftime("%d%m%Y")
        # 1st file (Begin Day) - C_VAR1_ddmmyyyy_1.DAT
        # 6th file (End Day)   - C_VAR1_ddmmyyyy_6.DAT

        suffix = '1' if file_type == 'BEGIN' else '6'
        url = f"{self.ARCHIVES_URL}/archives/nsccl/var/C_VAR1_{date_str}_{suffix}.DAT"

        resp = self.get(url)
        if resp.status_code == 200:
            # These are usually comma separated without header? Or with header?
            # Let's inspect content logic or assume standard CSV
            try:
                df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                # Ensure columns are stripped
                df.columns = [str(c).strip() for c in df.columns]
                return df
            except:
                pass
        return pd.DataFrame()

    def get_contract_delta(self, trade_date: date) -> pd.DataFrame:
        """Get Contract Delta."""
        # Archive URL: https://nsearchives.nseindia.com/archives/nsccl/delta/N_DELTA_TRD_ddmmyyyy.DAT
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/archives/nsccl/delta/N_DELTA_TRD_{date_str}.DAT"

        resp = self.get(url)
        if resp.status_code == 200:
            try:
                df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                df.columns = [str(c).strip() for c in df.columns]
                return df
            except:
                pass
        return pd.DataFrame()
