"""
backend/nselib/capital_market.py
"""
import io
import zipfile
import logging
import pandas as pd
from datetime import date
from .constants import ARCHIVES_URL, BASE_URL
from .lib import NseSession

logger = logging.getLogger(__name__)

class CapitalMarket:
    def __init__(self, session: NseSession):
        self.session = session

    def bhav_copy_equities(self, trade_date: date) -> pd.DataFrame:
        """
        Get CM Bhavcopy (Equity) - Uses sec_bhavdata_full for delivery info.
        URL Pattern: https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_ddmmyyyy.csv
        """
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{ARCHIVES_URL}/products/content/sec_bhavdata_full_{date_str}.csv"

        resp = self.session.get(url)
        if resp.status_code == 200:
            try:
                df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                # Clean columns: strip whitespace
                df.columns = [c.strip() for c in df.columns]
                return df
            except Exception as e:
                logger.error(f"Error parsing Equity Bhavcopy: {e}")
        return pd.DataFrame()

    def bulk_deal_data(self, trade_date: date) -> pd.DataFrame:
        """
        Get Bulk Deals via API.
        URL Pattern: https://www.nseindia.com/api/historicalOR/bulk-block-short-deals?optionType=bulk_deals&from=dd-mm-yyyy&to=dd-mm-yyyy&csv=true
        """
        date_str = trade_date.strftime("%d-%m-%Y")
        url = f"{BASE_URL}/api/historicalOR/bulk-block-short-deals"
        params = {
            'optionType': 'bulk_deals',
            'from': date_str,
            'to': date_str,
            'csv': 'true'
        }

        resp = self.session.get(url, params=params)
        if resp.status_code == 200:
            try:
                df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                df.columns = [c.strip() for c in df.columns]
                return df
            except Exception as e:
                logger.error(f"Error parsing Bulk Deals: {e}")
        return pd.DataFrame()

    def block_deals_data(self, trade_date: date) -> pd.DataFrame:
        """
        Get Block Deals via API.
        URL Pattern: https://www.nseindia.com/api/historicalOR/bulk-block-short-deals?optionType=block_deals&from=dd-mm-yyyy&to=dd-mm-yyyy&csv=true
        """
        date_str = trade_date.strftime("%d-%m-%Y")
        url = f"{BASE_URL}/api/historicalOR/bulk-block-short-deals"
        params = {
            'optionType': 'block_deals',
            'from': date_str,
            'to': date_str,
            'csv': 'true'
        }

        resp = self.session.get(url, params=params)
        if resp.status_code == 200:
            try:
                df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                df.columns = [c.strip() for c in df.columns]
                return df
            except Exception as e:
                logger.error(f"Error parsing Block Deals: {e}")
        return pd.DataFrame()

    def deliverable_position_data(self, trade_date: date) -> pd.DataFrame:
        """
        Get MTO Delivery Data (.DAT).
        URL Pattern: https://nsearchives.nseindia.com/archives/equities/mto/MTO_ddmmyyyy.DAT
        """
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{ARCHIVES_URL}/archives/equities/mto/MTO_{date_str}.DAT"

        resp = self.session.get(url)
        if resp.status_code == 200:
            try:
                content = resp.content.decode('utf-8', errors='ignore')
                lines = content.strip().split('\n')

                # Robust logic: Find header line starting with "Record Type"
                header_idx = -1
                for i, line in enumerate(lines[:20]): # Check first 20 lines
                    if "Record Type" in line and "Name of Security" in line:
                        header_idx = i
                        break

                if header_idx != -1 and len(lines) > header_idx + 1:
                    header = lines[header_idx]
                    data = lines[header_idx+1:]
                    # Ensure consistent CSV format
                    csv_str = header + '\n' + '\n'.join(data)
                    df = pd.read_csv(io.StringIO(csv_str), low_memory=False)
                    df.columns = [c.strip() for c in df.columns]
                    return df
            except Exception as e:
                logger.error(f"Error parsing MTO Delivery Data: {e}")
        return pd.DataFrame()

    def market_watch_all_indices(self, trade_date: date) -> pd.DataFrame:
        """
        Get MWPL Client Position Data (Excel).
        URL Pattern: https://nsearchives.nseindia.com/archives/equities/mto/mwpl_cli_ddmmyyyy.xls
        """
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{ARCHIVES_URL}/archives/equities/mto/mwpl_cli_{date_str}.xls"

        resp = self.session.get(url)
        if resp.status_code == 200:
            try:
                # Header is often in row 2 (index 1)
                # openpyxl is required for xlsx, xlrd for xls.
                # Assuming appropriate engine is installed or auto-detected.
                df = pd.read_excel(io.BytesIO(resp.content), header=1)
                df.columns = [str(c).strip() for c in df.columns]
                return df
            except Exception as e:
                logger.error(f"Error parsing MWPL Data: {e}")
        return pd.DataFrame()

    def pe_ratio_data(self, trade_date: date) -> pd.DataFrame:
        """
        Get P/E Ratio Data (Indices).
        URL Pattern: https://nsearchives.nseindia.com/content/indices/ind_close_all_ddmmyyyy.csv
        """
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{ARCHIVES_URL}/content/indices/ind_close_all_{date_str}.csv"

        resp = self.session.get(url)
        if resp.status_code == 200:
            try:
                df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                df.columns = [c.strip() for c in df.columns]
                return df
            except Exception as e:
                logger.error(f"Error parsing PE Ratio Data: {e}")
        return pd.DataFrame()
