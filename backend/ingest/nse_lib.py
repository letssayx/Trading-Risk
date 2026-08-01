"""NSE Library Adapter - Re-implementation of nselib logic"""
from curl_cffi import requests as cffi_requests
import pandas as pd
from backend.ingest.parse_pdf import extract_amount_from_pdf
import io
import zipfile
import logging
import os
from datetime import date, datetime
from typing import Optional, Any

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
        self.session = cffi_requests.Session(impersonate="chrome110")
        self.session.headers.update(self.HEADERS)
        self._cookies_primed = False

    def _ensure_session(self):
        """Prime cookies if not already done. Retries to avoid Connection timeouts."""
        import time
        if self._cookies_primed:
            return

        for attempt in range(1, 4):
            try:
                logger.info(f"Priming NSE session via {self.BASE_URL}... (Attempt {attempt})")
                # Minimal headers for initial handshake often helps
                headers = {
                    'User-Agent': self.HEADERS['User-Agent'],
                    'Accept': '*/*',
                    'Connection': 'keep-alive'
                }
                # Timeout reduced significantly to prevent hanging
                resp = self.session.get(self.BASE_URL, headers=headers, timeout=5)
                if resp.status_code == 200:
                    self._cookies_primed = True
                    logger.info("Session primed successfully.")
                    return
                else:
                    logger.warning(f"Session prime failed: {resp.status_code}")
            except Exception as e:
                logger.error(f"Session prime error on attempt {attempt}: {e}")

            time.sleep(2 * attempt)

        logger.error("Failed to prime NSE session after 3 attempts.")

    def get(self, url: str, use_curl: bool = False) -> Any:
        """Execute GET request with session handling."""
        if use_curl:
            try:
                # Use curl_cffi to bypass Bot protections (e.g. for archives and static CSVs)
                return cffi_requests.get(url, impersonate="chrome110", timeout=30, headers=self.HEADERS)
            except Exception as e:
                logger.warning(f"curl_cffi get failed for {url}, falling back to standard requests: {e}")
                import requests as std_requests
                try:
                    resp = std_requests.get(url, headers=self.HEADERS, timeout=30)
                    if resp.status_code == 200:
                        return resp
                except:
                    pass
                return None

        self._ensure_session()


        # Ensure Referer is set for API calls
        if 'api' in url and 'Referer' not in self.session.headers:
            self.session.headers['Referer'] = self.BASE_URL

        try:
            try:
                resp = self.session.get(url, timeout=15)
            except Exception as e:
                logger.warning(f"session.get failed for {url}, recreating session: {e}")
                self.session = cffi_requests.Session(impersonate="chrome110")
                self.session.headers.update(self.HEADERS)
                self._cookies_primed = False
                self._ensure_session()
                resp = self.session.get(url, timeout=15)

            # Retry on 401/403 once
            if resp.status_code in (401, 403):
                logger.warning(f"Got {resp.status_code}, re-priming session...")
                self._cookies_primed = False
                self.session.cookies.clear()
                self._ensure_session()
                resp = self.session.get(url, timeout=15)

            return resp
        except Exception as e:
            logger.error(f"Error executing GET {url}: {e}")
            return None

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
                # The MTO .DAT file has 6 header columns but 7 data columns (the 4th is 'Series' but missing from header)
                # 'Record Type,Sr No,Name of Security,Quantity Traded,Deliverable Quantity,% of Deliverable'
                # vs '20,1,0MOFSL27,N3,285,200,70.18'
                header = lines[header_idx]
                if header.count(',') == 5 and lines[header_idx+1].count(',') == 6:
                    parts = header.split(',')
                    parts.insert(3, 'Series')
                    header = ','.join(parts)

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

    def parse_pe_ratio(self, content: bytes) -> pd.DataFrame:
        """Parse P/E Ratio CSV content."""
        try:
            df = pd.read_csv(io.BytesIO(content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"P/E Ratio parse error: {e}")
            return pd.DataFrame()

    def parse_pe_ratio_idx(self, content: bytes) -> pd.DataFrame:
        """Parse Index P/E Ratio CSV content."""
        try:
            df = pd.read_csv(io.BytesIO(content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"Index P/E Ratio parse error: {e}")
            return pd.DataFrame()

    def parse_india_vix(self, content: bytes) -> pd.DataFrame:
        """Parse India VIX CSV content."""
        try:
            df = pd.read_csv(io.BytesIO(content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"India VIX parse error: {e}")
            return pd.DataFrame()

    def parse_corporate_actions(self, content: bytes) -> pd.DataFrame:
        """Parse Corporate Actions CSV content."""
        try:
            df = pd.read_csv(io.BytesIO(content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"Corporate Actions parse error: {e}")
            return pd.DataFrame()

    def parse_board_meetings(self, content: bytes) -> pd.DataFrame:
        """Parse Board Meetings CSV content."""
        try:
            df = pd.read_csv(io.BytesIO(content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"Board Meetings parse error: {e}")
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
            return self.parse_pe_ratio(resp.content)
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
            return self.parse_pe_ratio(resp.content)
        return pd.DataFrame()

    def get_mto_delivery(self, trade_date: date) -> pd.DataFrame:
        """Get MTO Delivery Data (.DAT)."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/archives/equities/mto/MTO_{date_str}.DAT"

        resp = self.get(url)
        if resp.status_code == 200:
            return self.parse_mto(resp.content)

        return pd.DataFrame()

    def get_pe_ratio_idx(self, trade_date: date) -> pd.DataFrame:
        """Get P/E Ratio Data (Indices)."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/content/indices/ind_close_all_{date_str}.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            return self.parse_pe_ratio_idx(resp.content)

        return pd.DataFrame()

    def get_historical_index_data(self, trade_date: date) -> pd.DataFrame:
        """Get Historical Index Data (Spot Prices)."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/content/indices/ind_close_all_{date_str}.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            try:
                df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                df.columns = [c.strip() for c in df.columns]
                return df
            except Exception as e:
                logger.error(f"Historical Index Data parse error: {e}")
        return pd.DataFrame()

    def get_india_vix(self, trade_date: date) -> pd.DataFrame:
        """Get India VIX Data (from Indices file)."""
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{self.ARCHIVES_URL}/content/indices/ind_close_all_{date_str}.csv"

        resp = self.get(url)
        if resp.status_code == 200:
            return self.parse_india_vix(resp.content)

        return pd.DataFrame()

    def get_mwpl(self, trade_date: date) -> pd.DataFrame:
        """Get MWPL Data (Excel)."""
        date_str = trade_date.strftime("%d%m%Y")
        base_filename = f"mwpl_cli_{date_str}"
        url = f"{self.ARCHIVES_URL}/content/nsccl/{base_filename}.xls"

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
        url = f"{self.ARCHIVES_URL}/content/cm/NSE_CM_security_{date_str}.csv.gz"

        resp = self.get(url)
        if resp.status_code == 200:
            import gzip
            content = gzip.decompress(resp.content)
            df = pd.read_csv(io.BytesIO(content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df

        # Fallback to plain csv if gz is missing
        url_csv = f"{self.ARCHIVES_URL}/content/cm/NSE_CM_security_{date_str}.csv"
        resp_csv = self.get(url_csv)
        if resp_csv.status_code == 200:
            df = pd.read_csv(io.BytesIO(resp_csv.content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df

        return pd.DataFrame()

    def get_pe_ratio(self, trade_date: date) -> pd.DataFrame:
        """Get P/E Ratio Data (Equities)."""
        date_str_short = trade_date.strftime("%d%m%y")
        date_str_long = trade_date.strftime("%d%m%Y")

        urls = [
            f"{self.ARCHIVES_URL}/content/equities/peDetail/PE_{date_str_long}.csv",
            f"{self.ARCHIVES_URL}/content/equities/peDetail/pe_{date_str_long}.csv",
            f"{self.ARCHIVES_URL}/content/equities/peDetail/PE_{date_str_short}.csv",
            f"{self.ARCHIVES_URL}/content/equities/peDetail/pe_{date_str_short}.csv",
            f"{self.ARCHIVES_URL}/archives/equities/pe/pe_{date_str_long}.csv",
            f"{self.ARCHIVES_URL}/archives/equities/pe/PE_{date_str_long}.csv"
        ]

        for url in urls:
            resp = self.get(url)
            if resp.status_code == 200:
                df = self.parse_pe_ratio(resp.content)
                if not df.empty:
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

    def get_board_meetings(self, trade_date: date) -> pd.DataFrame:
        """Get Board Meetings."""
        from datetime import timedelta, datetime
        import re

        # Strict daily fetch
        from_date_str = trade_date.strftime("%d-%m-%Y")
        to_date_str = trade_date.strftime("%d-%m-%Y")
        url = f"{self.BASE_URL}/api/corporate-board-meetings?index=equities&from_date={from_date_str}&to_date={to_date_str}"

        resp = self.get(url)
        if resp is None:
            return pd.DataFrame()

        if resp.status_code == 200:
            try:
                # The JSON endpoint actually respects historical dates
                data = resp.json()
                if not data:
                     return pd.DataFrame()

                dedup_bm = []
                seen_bm = set()
                for item in data:
                    dedup_key = f"{item.get('bm_symbol')}_{item.get('bm_date')}_{item.get('bm_purpose')}"
                    if dedup_key not in seen_bm:
                        seen_bm.add(dedup_key)
                        dedup_bm.append(item)
                data = dedup_bm

                # Get all CA events globally in one request rather than N+1
                ca_url = f"{self.BASE_URL}/api/corporates-corporateActions?index=equities&from_date={from_date_str}&to_date={to_date_str}"
                ca_resp = self.get(ca_url)
                ca_data = []
                if ca_resp and ca_resp.status_code == 200:
                    try:
                        ca_data = ca_resp.json()
                    except Exception as e:
                        logger.error(f"Failed to parse global CA response: {e}")

                # Get corporate announcements globally to extract XBRL attachment texts
                # This has the actual "Rs 54" amounts and record dates for announcements without CA entries yet
                announcement_url_div = f"{self.BASE_URL}/api/corporate-announcements?index=equities&subject=Dividend"
                announcement_url_rec = f"{self.BASE_URL}/api/corporate-announcements?index=equities&subject=Record%20Date"
                announcement_url_agm = f"{self.BASE_URL}/api/corporate-announcements?index=equities&from_date={from_date_str}&to_date={to_date_str}"
                announcement_url_fin = f"{self.BASE_URL}/api/corporate-announcements?index=equities&subject=Financial%20Results"
                announcement_url_out = f"{self.BASE_URL}/api/corporate-announcements?index=equities&from_date={from_date_str}&to_date={to_date_str}"

                div_announcements = []
                rec_announcements = []
                agm_announcements = []
                fin_announcements = []
                out_announcements = []

                resp_div = self.get(announcement_url_div)
                if resp_div and resp_div.status_code == 200:
                    try:
                        div_announcements = resp_div.json()
                    except Exception as e:
                        logger.error(f"Failed to parse dividend announcements: {e}")

                resp_rec = self.get(announcement_url_rec)
                if resp_rec and resp_rec.status_code == 200:
                    try:
                        rec_announcements = resp_rec.json()
                    except Exception as e:
                        logger.error(f"Failed to parse record date announcements: {e}")

                resp_agm = self.get(announcement_url_agm)
                if resp_agm and resp_agm.status_code == 200:
                    try:
                        agm_data = resp_agm.json()
                        agm_announcements = []
                        for ann in (agm_data if isinstance(agm_data, list) else []):
                            subj = str(ann.get('subject', '')).lower()
                            desc = str(ann.get('desc', '')).lower()
                            if 'agm' in subj or 'annual general meeting' in subj or 'shareholders meeting' in subj or 'agm' in desc or 'annual general meeting' in desc or 'shareholders meeting' in desc:
                                if 'dividend' in subj or 'dividend' in desc:
                                    agm_announcements.append(ann)
                    except Exception as e:
                        logger.error(f"Failed to parse AGM announcements: {e}")

                resp_fin = self.get(announcement_url_fin)
                if resp_fin and resp_fin.status_code == 200:
                    try:
                        fin_announcements = resp_fin.json()
                    except Exception as e:
                        logger.error(f"Failed to parse Financial Results announcements: {e}")

                # To prevent scraping thousands of PDFs for unrelated symbols, we extract the target symbols from the fetched board meetings
                target_symbols = set([item.get('bm_symbol') for item in data if item.get('bm_symbol')])
                for ca in ca_data:
                    sym = ca.get('symbol')
                    if sym:
                        target_symbols.add(sym)

                resp_out = self.get(announcement_url_out)
                if resp_out and resp_out.status_code == 200:
                    try:
                        all_out = resp_out.json()
                        if isinstance(all_out, list):
                            # Filter to only Outcome of Board Meeting to save memory/processing.
                            # However, memory instructs us to NOT restrict to just 'Outcome' because NSE frequently miscategorizes them under 'General Updates' or 'None'
                            # Still, we will keep them if they might contain 'Outcome' or are simply in the all_out list if needed,
                            # but let's fetch all general announcements on the specific date later if needed.
                            # Actually, per memory: "cross-reference all global corporate announcements for the date range on the NSE /api/corporate-announcements endpoint (without restricting to specific subject filters), because outcome PDFs containing dividends are frequently miscategorized"
                            # CRITICAL FIX: Only collect announcements for symbols we are actually processing board meetings for to avoid downloading every company's PDF
                            out_announcements = [a for a in all_out if a.get('symbol') in target_symbols]
                    except Exception as e:
                        logger.error(f"Failed to parse outcome announcements: {e}")

                # Build lookup dictionaries by symbol
                symbol_announcements = {}

                for ann in div_announcements + rec_announcements + agm_announcements + fin_announcements + out_announcements:
                    sym = ann.get('symbol')
                    if sym and sym in target_symbols:
                        if sym not in symbol_announcements:
                            symbol_announcements[sym] = []
                        symbol_announcements[sym].append(ann)

                # Build a mapping of symbol -> list of dividend CA events
                symbol_ca_map = {}
                for ca in ca_data:
                    subject = str(ca.get('subject', '')).lower()
                    if 'dividend' in subject:
                        sym = ca.get('symbol')
                        if sym:
                            if sym not in symbol_ca_map:
                                symbol_ca_map[sym] = []
                            symbol_ca_map[sym].append(ca)





                enriched_data = []
                consumed_announcements = set()

                for item in data:
                    item['EXTRACTED_DIVIDEND_AMOUNT'] = None
                    item['EXTRACTED_DIVIDEND_TYPE'] = None
                    item['EXTRACTED_RECORD_DATE'] = None

                    purpose = str(item.get('bm_purpose', '')).lower()
                    desc = str(item.get('bm_desc', '')).lower()
                    symbol = item.get('bm_symbol')

                    has_dividend_mention = 'dividend' in purpose or 'dividend' in desc or 'intdiv' in purpose or 'int div' in purpose or 'intdiv' in desc or 'int div' in desc or 'findiv' in purpose or 'fin div' in purpose or 'findiv' in desc or 'fin div' in desc

                    try:
                        bm_date_obj_check = datetime.strptime(item.get('bm_date', ''), "%d-%b-%Y").date()
                    except ValueError:
                        bm_date_obj_check = None

                    is_agm = 'annual general meeting' in purpose or 'agm' in purpose

                    matched_anns = []
                    if symbol and symbol in symbol_announcements and bm_date_obj_check:
                        for ann in symbol_announcements[symbol]:
                            subj = str(ann.get('subject', '')).lower()
                            if 'dividend' in subj or 'record date' in subj:
                                ann_date_str = ann.get('an_dt', '')
                                try:
                                    ann_date_obj = datetime.strptime(ann_date_str.split(' ')[0], "%d-%b-%Y").date()
                                    if 0 <= (ann_date_obj - bm_date_obj_check).days <= 3:
                                        has_dividend_mention = True
                                        matched_anns.append(ann)
                                        consumed_announcements.add(ann.get('seq_id'))
                                except ValueError:
                                    pass
                            elif 'shareholders meeting' in subj or 'agm' in subj or 'annual general meeting' in subj:
                                ann_date_str = ann.get('an_dt', '')
                                try:
                                    ann_date_obj = datetime.strptime(ann_date_str.split(' ')[0], "%d-%b-%Y").date()
                                    if 0 <= (ann_date_obj - bm_date_obj_check).days <= 3:
                                        is_agm = True
                                        matched_anns.append(ann)
                                        consumed_announcements.add(ann.get('seq_id'))
                                except ValueError:
                                    pass

                    if has_dividend_mention or is_agm:
                        base_type = 'Final' if ('final' in purpose or 'findiv' in purpose or 'fin div' in purpose) else ('Interim' if 'interim' in purpose or 'intdiv' in purpose or 'int div' in purpose or 'quarterly' in purpose or 'quarterly' in desc else ('Special' if 'special' in purpose else 'Dividend'))
                        if is_agm:
                            base_type = 'AGM'
                            item['bm_purpose'] = 'Annual General Meeting'

                        added_branches = False

                        if matched_anns:
                            for ann in matched_anns:
                                new_item = item.copy()
                                found_amount = None
                                found_record_date = None
                                found_type = base_type

                                attchmntText = ann.get('attchmntText', '')

                                xbrl_matches = re.findall(r'<[^>]*Dividend[^>]*>.*?Rs\.?\s*(\d+(?:\.\d+)?).*?</[^>]*>', attchmntText, re.IGNORECASE)
                                if not xbrl_matches:
                                    xbrl_matches = re.findall(r'<[^>]*Dividend[^>]*>.*?(\d+(?:\.\d+)?).*?</[^>]*>', attchmntText, re.IGNORECASE)
                                if xbrl_matches:
                                    found_amount = sum(float(m) for m in xbrl_matches)

                                if 'DateOfAnnualGeneralMeeting' in attchmntText or 'dateofannualgeneralmeeting' in attchmntText.lower():
                                    agm_date_match = re.search(r'<[^>]*DateOfAnnualGeneralMeeting[^>]*>.*?(\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{4}-\d{2}-\d{2}).*?</[^>]*>', attchmntText, re.IGNORECASE)
                                    if agm_date_match:
                                        new_item['EXTRACTED_AGM_DATE'] = agm_date_match.group(1)
                                        new_item['bm_purpose'] = str(new_item.get('bm_purpose') or '') + f" - AGM - {agm_date_match.group(1)}"

                                # Also check if standard date mentioned next to AGM
                                if not new_item.get('EXTRACTED_AGM_DATE'):
                                    fallback_agm = re.search(r'(?:agm|annual general meeting).*?(?:on|dated|scheduled for|-)?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]{3,9}\s+\d{4}|\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', text_lower, re.IGNORECASE)
                                    if fallback_agm:
                                        new_item['EXTRACTED_AGM_DATE'] = fallback_agm.group(1)
                                        new_item['bm_purpose'] = str(new_item.get('bm_purpose') or '') + f" - AGM - {fallback_agm.group(1)}"

                                if found_amount is None:
                                    _clean_text = re.sub(r'(?:face value|fv|paid-up capital|paid up capital|equity shares? of|shares? of)\s*(?:of\s*)?(?:rs\.?|re\.?|rupees?|inr|[-/]|\s|\u20b9)*\d+(?:\.\d+)?(?:/-)?(?:\s*each)?', '', attchmntText, flags=re.IGNORECASE)

                                    if 'including' in _clean_text.lower() or 'includes' in _clean_text.lower():
                                        match = re.search(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_text, re.IGNORECASE)
                                        if match:
                                            found_amount = float(match.group(1))
                                    else:
                                        div_pattern = re.compile(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', re.IGNORECASE)
                                        matches = div_pattern.findall(_clean_text)
                                        if matches:
                                            found_amount = sum(float(m) for m in matches)

                                subj = str(ann.get('subject', '')).lower()
                                desc_ann = str(ann.get('desc', '')).lower()
                                text_lower = attchmntText.lower() + " " + subj + " " + desc_ann
                                if 'interim' in text_lower or 'intdiv' in text_lower or 'int div' in text_lower: found_type = 'Interim'
                                elif 'final' in text_lower or 'finai' in text_lower or 'findiv' in text_lower or 'fin div' in text_lower: found_type = 'Final'
                                elif 'special' in text_lower: found_type = 'Special'
                                elif 'quarterly' in text_lower: found_type = 'Interim'

                                # Add AGM explicit regex check for text fallback if XML fails/404s
                                if re.search(r'\b(agm|annual general meeting)\b', text_lower):
                                    # Don't overwrite if it's already a dividend type we're specifically tracking
                                    if found_type == 'Dividend':
                                        found_type = 'AGM'

                                agm_m = re.search(r'(?:agm|annual general meeting).*?\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})\b', text_lower, re.IGNORECASE)
                                if agm_m:
                                    agm_date_str = agm_m.group(1).replace('\n', ' ').strip()
                                    try:
                                        new_item['EXTRACTED_AGM_DATE'] = pd.to_datetime(agm_date_str).strftime('%Y-%m-%d')
                                    except:
                                        pass


                                date_pattern = re.compile(r'(\d{1,2}-[a-zA-Z]{3}-\d{4})')
                                record_date_match = re.search(r'<[^>]*RecordDate[^>]*>.*?(\d{1,2}-[a-zA-Z]{3}-\d{4}).*?</[^>]*>', attchmntText, re.IGNORECASE)
                                if record_date_match:
                                    found_record_date = record_date_match.group(1)

                                if not found_record_date:
                                    ex_date_match = re.search(r'(?:ex-date|ex date).*?(\d{1,2}-[a-zA-Z]{3}-\d{4})', attchmntText, re.IGNORECASE)
                                    if ex_date_match:
                                        found_record_date = ex_date_match.group(1)

                                if not found_record_date:
                                    date_match = date_pattern.search(attchmntText)
                                    if date_match and 'record date' in text_lower:
                                        found_record_date = date_match.group(1)

                                if found_amount:
                                    new_item['EXTRACTED_DIVIDEND_AMOUNT'] = found_amount
                                    new_item['EXTRACTED_DIVIDEND_TYPE'] = found_type
                                if found_record_date:
                                    new_item['EXTRACTED_RECORD_DATE'] = found_record_date

                                if found_amount or found_record_date:
                                    is_dup = False
                                    for e in enriched_data:
                                        if e.get('bm_symbol') == new_item['bm_symbol'] and e.get('EXTRACTED_RECORD_DATE') == new_item['EXTRACTED_RECORD_DATE'] and e.get('EXTRACTED_DIVIDEND_TYPE') == new_item['EXTRACTED_DIVIDEND_TYPE']:
                                            is_dup = True
                                            break
                                    if not is_dup:
                                        enriched_data.append(new_item)
                                        added_branches = True

                        found_amount = None
                        found_record_date = None
                        found_type = base_type

                        if symbol and symbol in symbol_ca_map:
                            try:
                                bm_date_obj = datetime.strptime(item.get('bm_date', ''), "%d-%b-%Y").date()
                            except ValueError:
                                bm_date_obj = None

                            for ca in symbol_ca_map[symbol]:
                                ca_ex_date_str = str(ca.get('exDate', ''))
                                try:
                                    ca_ex_date_obj = datetime.strptime(ca_ex_date_str, "%d-%b-%Y").date()
                                except ValueError:
                                    ca_ex_date_obj = None

                                if bm_date_obj and ca_ex_date_obj:
                                    days_diff = (ca_ex_date_obj - bm_date_obj).days
                                    if days_diff < -1:
                                        continue

                                subject = str(ca.get('subject', ''))

                                _clean_subject = re.sub(r'(?:face value|fv|paid-up capital|paid up capital|equity shares? of|shares? of)\s*(?:of\s*)?(?:rs\.?|re\.?|rupees?|inr|[-/]|\s|\u20b9)*\d+(?:\.\d+)?(?:/-)?(?:\s*each)?', '', subject, flags=re.IGNORECASE)
                                if 'including' in _clean_subject.lower() or 'includes' in _clean_subject.lower():
                                    match = re.search(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_subject, re.IGNORECASE)
                                    if match:
                                        found_amount = float(match.group(1))
                                else:
                                    matches = re.findall(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_subject, re.IGNORECASE)
                                    if matches:
                                        found_amount = sum(float(m) for m in matches)

                                if found_amount:
                                    if 'interim' in subject.lower() or 'intdiv' in subject.lower() or 'int div' in subject.lower() or 'quarterly' in subject.lower(): found_type = 'Interim'
                                    elif 'findiv' in subject.lower() or 'fin div' in subject.lower() or 'final' in subject.lower(): found_type = 'Final'
                                    elif 'special' in subject.lower(): found_type = 'Special'

                                rec_date = ca.get('recDate')
                                if rec_date and rec_date != '-':
                                    found_record_date = rec_date

                                if found_amount or found_record_date:
                                    break

                        if found_amount is None:
                            text_to_search = f"{purpose} {desc}"
                            _clean_text_2 = re.sub(r'(?:face value|fv|paid-up capital|paid up capital|equity shares? of|shares? of)\s*(?:of\s*)?(?:rs\.?|re\.?|rupees?|inr|[-/]|\s|\u20b9)*\d+(?:\.\d+)?(?:/-)?(?:\s*each)?', '', text_to_search, flags=re.IGNORECASE)

                            if 'including' in _clean_text_2.lower() or 'includes' in _clean_text_2.lower():
                                match = re.search(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_text_2, re.IGNORECASE)
                                if match:
                                    found_amount = float(match.group(1))
                            else:
                                ui_patterns = [
                                    r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)',
                                    r'(\d+(?:\.\d+)?)\s*\/\-',
                                    r'(?:dividend|int\s*div)\s+of\s+(\d+(?:\.\d+)?)',
                                    r'(?:dividend|int\s*div).*?\s+(\d+(?:\.\d+)?)\s+per'
                                ]
                                for pat in ui_patterns:
                                    matches = re.findall(pat, _clean_text_2, re.IGNORECASE)
                                    if matches:
                                        found_amount = sum(float(m) for m in matches)
                                        break

                            if found_amount or found_type == 'Dividend':
                                if 'interim' in text_to_search.lower() or 'intdiv' in text_to_search.lower() or 'int div' in text_to_search.lower() or 'quarterly' in text_to_search.lower(): found_type = 'Interim'
                                elif 'findiv' in text_to_search.lower() or 'fin div' in text_to_search.lower() or 'final' in text_to_search.lower() or 'finai' in text_to_search.lower(): found_type = 'Final'
                                elif re.search(r'\b(agm|annual general meeting)\b', text_to_search.lower()):
                                    if found_type == 'Dividend': found_type = 'AGM'
                                elif 'special' in text_to_search.lower(): found_type = 'Special'

                            agm_m2 = re.search(r'(?:agm|annual general meeting).*?\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})\b', text_to_search, re.IGNORECASE)
                            if agm_m2:
                                agm_date_str2 = agm_m2.group(1).replace('\n', ' ').strip()
                                try:
                                    item['EXTRACTED_AGM_DATE'] = pd.to_datetime(agm_date_str2).strftime('%Y-%m-%d')
                                except:
                                    pass

                        if (found_amount is None or found_record_date is None or found_type == 'Dividend') and bm_date_obj_check and bm_date_obj_check == trade_date:
                            attachment_url = str(item.get('ATTACHMENT', ''))
                            if attachment_url.startswith('http'):
                                pdf_amount, pdf_record_date, pdf_type, pdf_agm_date = extract_amount_from_pdf(attachment_url)
                                if pdf_amount and found_amount is None:
                                    found_amount = pdf_amount
                                if pdf_record_date and found_record_date is None:
                                    found_record_date = pdf_record_date
                                if pdf_type and found_type == 'Dividend':
                                    found_type = pdf_type
                                if pdf_agm_date:
                                    item['EXTRACTED_AGM_DATE'] = pdf_agm_date

                        if found_amount:
                            item['EXTRACTED_DIVIDEND_AMOUNT'] = found_amount
                            item['EXTRACTED_DIVIDEND_TYPE'] = found_type
                        if found_record_date:
                            item['EXTRACTED_RECORD_DATE'] = found_record_date

                        if not added_branches or found_amount or found_record_date:
                            is_dup = False
                            for e in enriched_data:
                                if e.get('bm_symbol') == item['bm_symbol'] and e.get('EXTRACTED_RECORD_DATE') == item['EXTRACTED_RECORD_DATE'] and e.get('EXTRACTED_DIVIDEND_TYPE') == item['EXTRACTED_DIVIDEND_TYPE'] and e.get('EXTRACTED_DIVIDEND_AMOUNT') == item['EXTRACTED_DIVIDEND_AMOUNT']:
                                    is_dup = True
                                    break
                            if not is_dup:
                                enriched_data.append(item)
                    else:
                        enriched_data.append(item)

                # Finally, synthesize standalone announcements (like COALINDIA General Updates for AGM/Record Date) that were missed
                for sym, anns in symbol_announcements.items():
                    for ann in anns:
                        if ann.get('seq_id') in consumed_announcements:
                            continue

                        subj = str(ann.get('subject', '')).lower()
                        desc = str(ann.get('desc', '')).lower()
                        attchmntText = str(ann.get('attchmntText', '')).lower()

                        has_div = 'dividend' in subj or 'dividend' in desc or 'dividend' in attchmntText
                        has_rd = 'record date' in subj or 'record date' in desc or 'record date' in attchmntText
                        is_agm = 'agm' in subj or 'annual general meeting' in subj or 'agm' in desc or 'annual general meeting' in desc or 'agm' in attchmntText or 'annual general meeting' in attchmntText

                        if has_div or has_rd or is_agm:
                            found_amount = None
                            found_record_date = None
                            found_type = 'Final'

                            text_lower = attchmntText + " " + subj + " " + desc
                            if 'interim' in text_lower or 'intdiv' in text_lower or 'quarterly' in text_lower: found_type = 'Interim'
                            elif 'final' in text_lower or 'findiv' in text_lower: found_type = 'Final'
                            elif 'special' in text_lower: found_type = 'Special'
                            else: found_type = 'Dividend' # Don't guess Final

                            xbrl_matches = re.findall(r'<[^>]*Dividend[^>]*>.*?Rs\.?\s*(\d+(?:\.\d+)?).*?</[^>]*>', attchmntText, re.IGNORECASE)
                            if not xbrl_matches:
                                xbrl_matches = re.findall(r'<[^>]*Dividend[^>]*>.*?(\d+(?:\.\d+)?).*?</[^>]*>', attchmntText, re.IGNORECASE)
                            if xbrl_matches:
                                found_amount = sum(float(m) for m in xbrl_matches)

                            bm_purpose = "General Updates"
                            if is_agm:
                                found_type = 'AGM'
                                bm_purpose = 'Annual General Meeting'
                                agm_date = None
                                if 'dateofannualgeneralmeeting' in attchmntText:
                                    agm_date_match = re.search(r'<[^>]*DateOfAnnualGeneralMeeting[^>]*>.*?(\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{4}-\d{2}-\d{2}).*?</[^>]*>', attchmntText, re.IGNORECASE)
                                    if agm_date_match:
                                        agm_date = agm_date_match.group(1)
                                        bm_purpose += f" - AGM - {agm_date}"

                                if not agm_date:
                                    fallback_agm = re.search(r'(?:agm|annual general meeting).*?(?:on|dated|scheduled for|-)?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]{3,9}\s+\d{4}|\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', text_lower, re.IGNORECASE)
                                    if fallback_agm:
                                        agm_date = fallback_agm.group(1)
                                        bm_purpose += f" - AGM - {agm_date}"

                            if found_amount is None:
                                _clean_text = re.sub(r'(?:face value|fv|paid-up capital|paid up capital|equity shares? of|shares? of)\s*(?:of\s*)?(?:rs\.?|re\.?|rupees?|inr|[-/]|\s|\u20b9)*\d+(?:\.\d+)?(?:/-)?(?:\s*each)?', '', attchmntText, flags=re.IGNORECASE)
                                if 'including' in _clean_text or 'includes' in _clean_text:
                                    match = re.search(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_text, re.IGNORECASE)
                                    if match: found_amount = float(match.group(1))
                                else:
                                    matches = re.findall(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_text, re.IGNORECASE)
                                    if matches: found_amount = sum(float(m) for m in matches)

                            date_pattern = re.compile(r'(\d{1,2}-[a-zA-Z]{3}-\d{4})')
                            record_date_match = re.search(r'<[^>]*RecordDate[^>]*>.*?(\d{1,2}-[a-zA-Z]{3}-\d{4}).*?</[^>]*>', attchmntText, re.IGNORECASE)
                            if record_date_match:
                                found_record_date = record_date_match.group(1)

                            if not found_record_date:
                                ex_date_match = re.search(r'(?:ex-date|ex date).*?(\d{1,2}-[a-zA-Z]{3}-\d{4})', attchmntText, re.IGNORECASE)
                                if ex_date_match:
                                    found_record_date = ex_date_match.group(1)

                            if not found_record_date:
                                date_match = date_pattern.search(attchmntText)
                                if date_match and 'record date' in text_lower:
                                    found_record_date = date_match.group(1)

                            if not found_record_date and 'record date' in text_lower:
                                fallback_rd = re.search(r'(?:record date|fixed).*?(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]{3,9}\s+\d{4}|\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', text_lower, re.IGNORECASE)
                                if fallback_rd:
                                    found_record_date = fallback_rd.group(1).replace('st ', ' ').replace('nd ', ' ').replace('rd ', ' ').replace('th ', ' ')

                            if found_amount or found_record_date or is_agm:
                                try:
                                    dt = datetime.strptime(ann.get('an_dt', '').split(' ')[0], "%d-%b-%Y")
                                    bm_date_str = dt.strftime("%d-%b-%Y")
                                except:
                                    bm_date_str = trade_date.strftime("%d-%b-%Y")

                                syn_item = {
                                    'bm_symbol': sym,
                                    'sm_name': ann.get('sm_name', ''),
                                    'bm_purpose': bm_purpose,
                                    'bm_desc': ann.get('attchmntText', ''),
                                    'bm_date': bm_date_str,
                                    'bm_timestamp': ann.get('an_dt', ''),
                                    'sysTime': ann.get('an_dt', ''),
                                    'ATTACHMENT': ann.get('attchmntFile', ''),
                                    'EXTRACTED_DIVIDEND_AMOUNT': found_amount,
                                    'EXTRACTED_DIVIDEND_TYPE': found_type,
                                    'EXTRACTED_RECORD_DATE': found_record_date
                                }
                                is_dup = False
                                for e in enriched_data:
                                    if e.get('bm_symbol') == syn_item['bm_symbol'] and e.get('EXTRACTED_RECORD_DATE') == syn_item['EXTRACTED_RECORD_DATE'] and e.get('EXTRACTED_DIVIDEND_TYPE') == syn_item['EXTRACTED_DIVIDEND_TYPE'] and e.get('EXTRACTED_DIVIDEND_AMOUNT') == syn_item['EXTRACTED_DIVIDEND_AMOUNT']:
                                        is_dup = True
                                        break
                                if not is_dup:
                                    enriched_data.append(syn_item)

                df = pd.DataFrame(enriched_data)
                mapping = {
                    'bm_symbol': 'SYMBOL',
                    'sm_name': 'COMPANY NAME',
                    'bm_purpose': 'PURPOSE',
                    'bm_desc': 'BM_DESC',
                    'bm_date': 'MEETING DATE',
                    'bm_timestamp': 'BROADCAST DATE',
                    'sysTime': 'SYSTIME',
                    'ATTACHMENT': 'ATTACHMENT'
                }
                df = df.rename(columns=mapping)
                return df
            except Exception as e:
                logger.error(f"Board Meetings parse error: {e}")
        return pd.DataFrame()

    def get_corporate_actions(self, trade_date: date) -> pd.DataFrame:
        """Get Corporate Actions."""
        from datetime import timedelta
        # Strict daily fetch
        from_date_str = trade_date.strftime("%d-%m-%Y")
        to_date_str = trade_date.strftime("%d-%m-%Y")
        url = f"{self.BASE_URL}/api/corporates-corporateActions?index=equities&from_date={from_date_str}&to_date={to_date_str}"

        resp = self.get(url)
        if resp is None:
            return pd.DataFrame()

        if resp.status_code == 200:
            try:
                # The JSON endpoint actually respects historical dates
                data = resp.json()
                if not data:
                     return pd.DataFrame()

                dedup_data = []
                seen_events = set()
                for item in data:
                    # Some endpoints return identical broadcasts, deduplicate by Symbol + Date + Subject/Purpose
                    # For CA, date usually refers to exDate or broadcastDate. We use caBroadcastDate if available.
                    dedup_key = f"{item.get('symbol')}_{item.get('exDate') or item.get('caBroadcastDate')}_{item.get('subject')}"
                    if dedup_key not in seen_events:
                        seen_events.add(dedup_key)
                        dedup_data.append(item)

                df = pd.DataFrame(dedup_data)
                # Map expected JSON keys to the upper-case CSV format our FieldMapper expects
                mapping = {
                    'symbol': 'SYMBOL',
                    'comp': 'COMPANY NAME',
                    'series': 'SERIES',
                    'faceVal': 'FACE VALUE',
                    'subject': 'PURPOSE',
                    'exDate': 'EX-DATE',
                    'recDate': 'RECORD DATE',
                    'bcStartDate': 'BC START DATE',
                    'bcEndDate': 'BC END DATE',
                    'ndStartDate': 'ND START DATE',
                    'ndEndDate': 'ND END DATE',
                    'caBroadcastDate': 'BROADCAST DATE'
                }
                df = df.rename(columns=mapping)
                return df
            except Exception as e:
                logger.error(f"Corporate Actions parse error: {e}")
        return pd.DataFrame()

    def get_contract_delta(self, trade_date: date) -> pd.DataFrame:
        """Get Contract Delta."""
        # New URL format for NSE Option Delta report (NCL delta file)
        # Format: https://nsearchives.nseindia.com/archives/nsccl/delta/N_DELTA_TRD_YYYYMMDD.DAT or .csv
        date_str = trade_date.strftime("%d%m%Y")
        iso_date_str = trade_date.strftime("%Y%m%d")

        urls = [
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/N_DELTA_TRD_{iso_date_str}.DAT",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/n_delta_trd_{iso_date_str}.DAT",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/N_DELTA_TRD_{iso_date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/n_delta_trd_{iso_date_str}.csv",
            f"{self.ARCHIVES_URL}/content/nsccl/Contract_Delta_{date_str}.csv",
            f"{self.ARCHIVES_URL}/content/nsccl/contract_delta_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/Contract_Delta_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/contract_delta_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/N_DELTA_TRD_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/n_delta_trd_{date_str}.csv",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/N_DELTA_TRD_{date_str}.DAT",
            f"{self.ARCHIVES_URL}/archives/nsccl/delta/n_delta_trd_{date_str}.DAT",
        ]

        try:
            for url in urls:
                # First try with regular python requests session (which FO bhavcopy uses successfully)
                # as curl_cffi often fails when session isn't persisted properly
                resp = self.get(url, use_curl=False)
                if resp and resp.status_code == 200 and b'<!doctype html>' not in resp.content[:1024].lower() and b'<!DOCTYPE html>' not in resp.content[:1024]:
                    try:
                        df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                        df.columns = [str(c).strip() for c in df.columns]
                        if not df.empty:
                            return df
                    except Exception as e:
                        logger.error(f"Error parsing Contract Delta from {url} (regular session): {e}")

                # Fallback to curl_cffi
                resp = self.get(url, use_curl=True)
                # Check for 200 OK and explicitly ignore NSE's custom 404 HTML payloads
                if resp and resp.status_code == 200 and b'<!doctype html>' not in resp.content[:1024].lower() and b'<!DOCTYPE html>' not in resp.content[:1024]:
                    try:
                        df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                        df.columns = [str(c).strip() for c in df.columns]
                        if not df.empty:
                            return df
                    except Exception as e:
                        logger.error(f"Error parsing Contract Delta from {url}: {e}")
        except Exception as outer_e:
            logger.error(f"Unexpected error in get_contract_delta for {trade_date}: {outer_e}")

        return pd.DataFrame()

    def get_financial_results(self, trade_date: date) -> pd.DataFrame:
        """Fetch Financial Results from NSE Corporate Announcements."""
        from datetime import timedelta
        # Usually results come in during earning season, check a window
        from_date_str = trade_date.strftime("%d-%m-%Y")
        to_date_str = (trade_date + timedelta(days=7)).strftime("%d-%m-%Y")
        url = f"{self.BASE_URL}/api/corporates-financial-results?index=equities&period=Quarterly&from_date={from_date_str}&to_date={to_date_str}"

        resp = self.get(url, use_curl=True)
        if resp is None:
            return pd.DataFrame()

        if resp.status_code == 200:
            try:
                data = resp.json()
                if not data:
                    return pd.DataFrame()

                from backend.ingest.parse_financials import extract_financials_from_xbrl, extract_financials_from_pdf

                records = []
                for item in data:
                    reBasEPS = None
                    reDilEPS = None
                    netProfit = None

                    xbrl_url = item.get('xbrl')
                    att = item.get('attachment') or item.get('attchmntFile')

                    if xbrl_url and xbrl_url != '-' and 'nsearchives.nseindia.com' in xbrl_url:
                        eps, np = extract_financials_from_xbrl(xbrl_url)
                        if eps is not None:
                            reBasEPS = eps
                            reDilEPS = eps
                        if np is not None:
                            netProfit = np

                    if (reBasEPS is None or netProfit is None) and att and 'nsearchives.nseindia.com' in att:
                        eps, np = extract_financials_from_pdf(att)
                        if eps is not None and reBasEPS is None:
                            reBasEPS = eps
                            reDilEPS = eps
                        if np is not None and netProfit is None:
                            netProfit = np


                    symbol = item.get('symbol')
                    period = item.get('period') # e.g. Q1, Q2, Yearly
                    bdate = item.get('bm_timestamp', item.get('seqDate'))
                    pend = item.get('period_end_date', item.get('toDate'))
                    att = item.get('attachment')

                    bdate_obj = None
                    if bdate:
                        try:
                            import re
                            bdate_clean = re.sub(r'\.\d+', '', str(bdate)).strip()
                            bdate_obj = datetime.strptime(bdate_clean, "%d-%b-%Y %H:%M:%S").date()
                        except:
                            try:
                                bdate_obj = datetime.strptime(str(bdate).split(' ')[0], "%d-%b-%Y").date()
                            except:
                                bdate_obj = trade_date
                    else:
                        bdate_obj = trade_date

                    if symbol:
                        records.append({
                            'symbol': symbol,
                            'date': bdate_obj,
                            'period': period,
                            'period_end_date': pend,
                            'basic_eps': reBasEPS,
                            'diluted_eps': reDilEPS,
                            'net_profit': netProfit,
                            'attachment': att
                        })

                if records:
                    return pd.DataFrame(records)
            except Exception as e:
                logger.error(f"Financial Results parse error: {e}")

        return pd.DataFrame()

    def get_fii_dii_cash(self, trade_date: date) -> pd.DataFrame:
        """Fetch FII/DII Cash Market flow data."""
        # Use the new fiidii-archive API endpoint which works for historical data
        date_str = trade_date.strftime("%d-%m-%Y")
        url = f"https://www.nseindia.com/api/fiidii-archive?from={date_str}&to={date_str}"
        resp = self.get(url)

        is_valid_json = False
        if resp and resp.status_code == 200:
            try:
                resp_json = resp.json()
                is_valid_json = True
            except Exception:
                pass

        # Fallback to the daily API if historical is empty or fails
        if not is_valid_json:
            url = "https://www.nseindia.com/api/fiidiiTradeReact"
            resp = self.get(url)

        if not resp or resp.status_code != 200:
            logger.error(f"Failed to fetch FII/DII Cash Flow for {trade_date}")
            return pd.DataFrame()

        try:
            data = resp.json()
            # The archive API returns a list of items directly, each containing a 'category', 'date', 'buyValue', etc.
            # The daily API sometimes returns a dict with 'data' key or a nested list.
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            elif isinstance(data, list) and len(data) > 0 and 'category' not in data[0] and 'data' in data[0]:
                 data = data[0]['data']

            if not isinstance(data, list) or len(data) == 0:
                logger.warning(f"No FII/DII records found for {trade_date}")
                return pd.DataFrame()

            records = []

            from datetime import date, datetime

            # The API returns a list of dictionaries with categories.
            # For the archive API, the date might be in a 'date' field in format 'dd-MMM-yyyy'
            for item in data:
                # Check date match if date field exists
                item_date_str = item.get('date')
                if item_date_str:
                    try:
                        item_date = datetime.strptime(item_date_str, "%d-%b-%Y").date()
                        if item_date != trade_date:
                            continue
                    except ValueError:
                        pass

                cat = item.get('category')
                if not cat: continue
                if 'FII' in cat or 'FPI' in cat:
                    cat_name = 'FII'
                elif 'DII' in cat:
                    cat_name = 'DII'
                else:
                    continue

                records.append({
                    'trade_date': trade_date,
                    'category': cat_name,
                    'buy_value': float(item.get('buyValue', 0)),
                    'sell_value': float(item.get('sellValue', 0)),
                    'net_value': float(item.get('netValue', 0))
                })

            if not records:
                # Check if we skipped due to date mismatch
                if len(data) > 0 and 'date' in data[0]:
                    api_date_str = data[0]['date']
                    try:
                        api_date = datetime.strptime(api_date_str, "%d-%b-%Y").date()
                        logger.warning(f"FII/DII API returned data for {api_date}, skipping import for requested {trade_date}")
                    except ValueError:
                        pass
                else:
                    logger.warning(f"No FII/DII records parsed for {trade_date}")

                # If the list is empty, fallback to Arihant
                return self._fetch_arihant_fii_dii(trade_date)

            return pd.DataFrame(records)

        except Exception as e:
            logger.error(f"Error parsing FII/DII cash flow data: {e}")
            # Fallback to Arihant Scraper on exception
            return self._fetch_arihant_fii_dii(trade_date)

    def _fetch_arihant_fii_dii(self, trade_date: date) -> pd.DataFrame:
        """Fallback method to fetch FII/DII data using pure requests against Arihant Capital."""
        logger.warning(f"Falling back to Arihant Capital pure HTTP scraper for {trade_date}")

        records = []
        try:
            from bs4 import BeautifulSoup
            from curl_cffi import requests
            import re

            # Using 'www' subdomain is required to prevent ASP.NET from sending a pageRedirect on POST
            url = "https://www.arihantcapital.com/derivatives/fii-dii-trading-activities"
            session = requests.Session(impersonate="chrome110")

            # 1. Fetch GET to prime cookies and get ViewState
            resp = session.get(url, timeout=15)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch Arihant GET, status: {resp.status_code}")
                return pd.DataFrame()

            soup = BeautifulSoup(resp.content, "html.parser")

            # Extract all hidden inputs required for ASP.NET WebForms POST
            def extract_all_inputs(soup):
                inputs = {}
                for i in soup.find_all("input"):
                    name = i.get("name")
                    if name:
                        inputs[name] = i.get("value", "")
                for s in soup.find_all("select"):
                    name = s.get("name")
                    if name:
                        selected = s.find("option", selected=True)
                        if selected:
                            inputs[name] = selected.get("value", "")
                        else:
                            first = s.find("option")
                            inputs[name] = first.get("value", "") if first else ""
                return inputs

            base_data = extract_all_inputs(soup)
            date_str = trade_date.strftime("%Y-%m-%d")

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-MicrosoftAjax": "Delta=true",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://www.arihantcapital.com",
                "Referer": url,
            }

            categories = [("FII/FPI", "FII"), ("DII", "DII")]

            for option_val, cat_name in categories:
                data = base_data.copy()
                data.update({
                    "ctl00$scrptmanagr": "ctl00$ContentPlaceHolder1$UpdatePanelBigSch|ctl00$ContentPlaceHolder1$btnGo",
                    "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnGo",
                    "__EVENTARGUMENT": "",
                    "ctl00$ContentPlaceHolder1$DrpMobmenu": "DM",
                    "ctl00$ContentPlaceHolder1$menuDM": "/derivatives/fii-dii-trading-activities",
                    "ctl00$ContentPlaceHolder1$cattypeid": "cash",
                    "ctl00$ContentPlaceHolder1$fosubCatid": "index",
                    "ctl00$ContentPlaceHolder1$ddlSubCategory": option_val,
                    "ctl00$ContentPlaceHolder1$fromdate": date_str,
                    "ctl00$ContentPlaceHolder1$todate": date_str,
                    "__ASYNCPOST": "true"
                })

                try:
                    resp_post = session.post(url, data=data, headers=headers, timeout=15)
                    text = resp_post.content.decode('utf-8')

                    match = re.search(r'(<table.*?</table>)', text, re.IGNORECASE | re.DOTALL)
                    if match:
                        table_html = match.group(1)
                        table_soup = BeautifulSoup(table_html, "html.parser")
                        rows = table_soup.find_all('tr')

                        if len(rows) > 1:
                            tds = rows[1].find_all(['td', 'th'])
                            if len(tds) >= 4:
                                text_vals = [c.text.strip() for c in tds]
                                parsed_date_str = text_vals[0]

                                try:
                                    row_date = pd.to_datetime(parsed_date_str).date()
                                    if row_date == trade_date:
                                        buy_val = float(text_vals[1].replace(',', ''))
                                        sell_val = float(text_vals[2].replace(',', ''))
                                        net_val = float(text_vals[3].replace(',', ''))

                                        records.append({
                                            'trade_date': trade_date,
                                            'category': cat_name,
                                            'buy_value': buy_val,
                                            'sell_value': sell_val,
                                            'net_value': net_val
                                        })
                                    else:
                                        logger.warning(f"Arihant HTTP scraper: Row date {row_date} did not match requested {trade_date} for {cat_name}")
                                except Exception as d_e:
                                    logger.warning(f"Arihant HTTP scraper date parse error for {text_vals[0]}: {d_e}")
                    else:
                        logger.warning(f"Arihant HTTP scraper: Table not found in AJAX response for {cat_name}")

                except Exception as e_cat:
                    logger.error(f"Error HTTP scraping {cat_name} from Arihant: {e_cat}")

            if records:
                logger.info(f"Successfully scraped fallback FII/DII data from Arihant Capital for {trade_date}")
                return pd.DataFrame(records)
            else:
                logger.warning(f"No valid records extracted from Arihant Capital HTTP scraper for {trade_date}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error in Arihant pure HTTP fallback scraper: {e}")
            return pd.DataFrame()
