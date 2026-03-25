"""NSE Library Adapter - Re-implementation of nselib logic"""
import requests
from curl_cffi import requests as cffi_requests
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
                resp = self.session.get(self.BASE_URL, headers=headers, timeout=30)
                if resp.status_code == 200:
                    self._cookies_primed = True
                    logger.info("Session primed successfully.")
                    return
                else:
                    logger.warning(f"Session prime failed: {resp.status_code}")
            except Exception as e:
                logger.error(f"Session prime error on attempt {attempt}: {e}")

            time.sleep(5 * attempt)

        logger.error("Failed to prime NSE session after 3 attempts.")

    def get(self, url: str) -> Any:
        """Execute GET request with session handling."""
        self._ensure_session()

        # Ensure Referer is set for API calls
        if 'api' in url and 'Referer' not in self.session.headers:
            self.session.headers['Referer'] = self.BASE_URL

        try:
            resp = self.session.get(url, timeout=30)

            # Retry on 401/403 once
            if resp.status_code in (401, 403):
                logger.warning(f"Got {resp.status_code}, re-priming session...")
                self._cookies_primed = False
                self.session.cookies.clear()
                self._ensure_session()
                resp = self.session.get(url, timeout=30)

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
        date_str = trade_date.strftime("%d-%m-%Y")
        url = f"{self.BASE_URL}/api/corporate-board-meetings?index=equities&from_date={date_str}&to_date={date_str}"

        resp = self.get(url)
        if resp is None:
            return pd.DataFrame()

        if resp.status_code == 200:
            try:
                # The JSON endpoint actually respects historical dates
                data = resp.json()
                if not data:
                     return pd.DataFrame()
                df = pd.DataFrame(data)
                # Map expected JSON keys to the upper-case CSV format our FieldMapper expects
                mapping = {
                    'bm_symbol': 'SYMBOL',
                    'sm_name': 'COMPANY NAME',
                    'bm_purpose': 'PURPOSE',
                    'bm_desc': 'BM_DESC',
                    'bm_date': 'MEETING DATE',
                    'bm_timestamp': 'BROADCAST DATE',
                    'ATTACHMENT': 'ATTACHMENT'
                }
                df = df.rename(columns=mapping)
                return df
            except Exception as e:
                logger.error(f"Board Meetings parse error: {e}")
        return pd.DataFrame()

    def get_corporate_actions(self, trade_date: date) -> pd.DataFrame:
        """Get Corporate Actions."""
        date_str = trade_date.strftime("%d-%m-%Y")
        url = f"{self.BASE_URL}/api/corporates-corporateActions?index=equities&from_date={date_str}&to_date={date_str}"

        resp = self.get(url)
        if resp is None:
            return pd.DataFrame()

        if resp.status_code == 200:
            try:
                # The JSON endpoint actually respects historical dates
                data = resp.json()
                if not data:
                     return pd.DataFrame()
                df = pd.DataFrame(data)
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

            from datetime import datetime

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
        """Fallback method to fetch FII/DII data from Arihant Capital."""
        url = "https://www.arihantcapital.com/derivatives/fii-dii-trading-activities"
        try:
            from bs4 import BeautifulSoup
            from io import StringIO

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"Arihant fallback failed with status {resp.status_code}")
                return pd.DataFrame()

            soup = BeautifulSoup(resp.content, 'html.parser')
            tables = soup.find_all('table')
            if not tables or len(tables) < 2:
                logger.warning("No expected FII/DII tables found on Arihant FII/DII page.")
                return pd.DataFrame()

            records = []

            # Parse FII (Table 0)
            try:
                fii_df = pd.read_html(StringIO(str(tables[0])), flavor='bs4')[0]
                for _, row in fii_df.iterrows():
                    row_date_str = str(row.iloc[0]).strip()
                    try:
                        parsed_date = pd.to_datetime(row_date_str, format='mixed', dayfirst=True).date()
                        if parsed_date == trade_date:
                            records.append({
                                'trade_date': parsed_date,
                                'category': 'FII',
                                'buy_value': float(str(row.iloc[1]).replace(',', '')),
                                'sell_value': float(str(row.iloc[2]).replace(',', '')),
                                'net_value': float(str(row.iloc[3]).replace(',', ''))
                            })
                            break
                    except Exception:
                        continue
            except ValueError:
                pass

            # Simulate Arihant 'Go' button postback to fetch DII
            data = {}
            for inp in soup.find_all("input"):
                if inp.has_attr("name") and inp.has_attr("value"):
                    data[inp["name"]] = inp["value"]
                elif inp.has_attr("name"):
                    data[inp["name"]] = ""

            data["ctl00$ScriptManager1"] = "ctl00$ContentPlaceHolder1$UpdatePanelBigSch|ctl00$ContentPlaceHolder1$btnGo"
            data["ctl00$ContentPlaceHolder1$ddlSubCategory"] = "DII"
            data["ctl00$ContentPlaceHolder1$btnGo"] = "Go"
            data["__EVENTTARGET"] = ""
            data["__EVENTARGUMENT"] = ""
            data["__ASYNCPOST"] = "true"

            headers.update({
                "X-MicrosoftAjax": "Delta=true",
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            })

            try:
                session = requests.Session()
                post_resp = session.post(url, headers=headers, data=data, timeout=10)
                parts = post_resp.text.split('|')

                for i, part in enumerate(parts):
                    if len(part) > 200 and ("<table" in part.lower() or "tbody" in part.lower()):
                        start_idx = part.find("<table")
                        if start_idx != -1:
                            html_content = part[start_idx:]
                            df = pd.read_html(StringIO(html_content), flavor='bs4')[0]

                            for _, row in df.iterrows():
                                row_date_str = str(row.iloc[0]).strip()
                                try:
                                    parsed_date = pd.to_datetime(row_date_str, format='mixed', dayfirst=True).date()
                                    if parsed_date == trade_date:
                                        records.append({
                                            'trade_date': parsed_date,
                                            'category': 'DII',
                                            'buy_value': float(str(row.iloc[1]).replace(',', '')),
                                            'sell_value': float(str(row.iloc[2]).replace(',', '')),
                                            'net_value': float(str(row.iloc[3]).replace(',', ''))
                                        })
                                        break
                                except Exception:
                                    continue
                        break
            except Exception as e:
                logger.error(f"Failed to fetch DII Arihant data via postback: {e}")


            # Parse DII (Table 1)
            try:
                dii_df = pd.read_html(StringIO(str(tables[1])), flavor='bs4')[0]
                for _, row in dii_df.iterrows():
                    row_date_str = str(row.iloc[0]).strip()
                    try:
                        parsed_date = pd.to_datetime(row_date_str, format='mixed', dayfirst=True).date()
                        if parsed_date == trade_date:
                            records.append({
                                'trade_date': parsed_date,
                                'category': 'DII',
                                'buy_value': float(str(row.iloc[1]).replace(',', '')),
                                'sell_value': float(str(row.iloc[2]).replace(',', '')),
                                'net_value': float(str(row.iloc[3]).replace(',', ''))
                            })
                            break
                    except Exception:
                        continue
            except ValueError:
                pass

            if not records:
                logger.warning(f"No fallback Arihant FII/DII records found for {trade_date}")
                return pd.DataFrame()

            logger.info(f"Successfully scraped FII/DII fallback data from Arihant for {trade_date}")
            return pd.DataFrame(records)

        except Exception as e:
            logger.error(f"Error in Arihant FII/DII fallback: {e}")
            return pd.DataFrame()
