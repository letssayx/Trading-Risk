"""
backend/nselib/derivatives.py
"""
import io
import zipfile
import logging
import pandas as pd
from datetime import date
from .constants import ARCHIVES_URL
from .lib import NseSession

logger = logging.getLogger(__name__)

class Derivatives:
    def __init__(self, session: NseSession):
        self.session = session

    def fno_bhav_copy(self, trade_date: date) -> pd.DataFrame:
        """
        Get FO Bhavcopy.
        URL Pattern: https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_yyyymmdd_F_0000.csv.zip
        """
        date_str = trade_date.strftime("%Y%m%d")
        url = f"{ARCHIVES_URL}/content/fo/BhavCopy_NSE_FO_0_0_0_{date_str}_F_0000.csv.zip"

        resp = self.session.get(url)
        if resp.status_code == 200:
            try:
                with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                    csv_name = [n for n in zf.namelist() if n.lower().endswith('.csv')][0]
                    with zf.open(csv_name) as f:
                        df = pd.read_csv(f, low_memory=False)
                        df.columns = [c.strip() for c in df.columns]
                        return df
            except Exception as e:
                logger.error(f"Error parsing FO Bhavcopy: {e}")
        return pd.DataFrame()

    def participant_wise_open_interest(self, trade_date: date) -> pd.DataFrame:
        """
        Get Participant Wise Open Interest.
        URL Pattern: https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_ddmmyyyy.csv
        """
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{ARCHIVES_URL}/content/nsccl/fao_participant_oi_{date_str}.csv"

        resp = self.session.get(url)
        if resp.status_code == 200:
            try:
                content = resp.content.decode('utf-8', errors='ignore')
                # Skip metadata row if present
                lines = content.split('\n')
                skiprows = 0
                if len(lines) > 0 and "Participant wise Open Interest" in lines[0]:
                    skiprows = 1

                df = pd.read_csv(io.StringIO(content), skiprows=skiprows, low_memory=False)
                df.columns = [c.strip() for c in df.columns]
                return df
            except Exception as e:
                logger.error(f"Error parsing Participant OI: {e}")
        return pd.DataFrame()

    def fii_derivatives_statistics(self, trade_date: date) -> pd.DataFrame:
        """
        Get FII Derivatives Statistics (Excel).
        URL Pattern: https://nsearchives.nseindia.com/content/fo/fii_stats_dd-Mon-yyyy.xls
        """
        date_str = trade_date.strftime("%d-%b-%Y")
        url = f"{ARCHIVES_URL}/content/fo/fii_stats_{date_str}.xls"

        resp = self.session.get(url)
        if resp.status_code == 200:
            try:
                df = pd.read_excel(io.BytesIO(resp.content))
                # Usually no header issues here, but stripping is safe
                df.columns = [str(c).strip() for c in df.columns]
                return df
            except Exception as e:
                logger.error(f"Error parsing FII Stats: {e}")
        return pd.DataFrame()

    def fo_volatility(self, trade_date: date) -> pd.DataFrame:
        """
        Get FO Volatility.
        URL Pattern: https://nsearchives.nseindia.com/archives/nsccl/volt/FOVOLT_ddmmyyyy.csv
        """
        date_str = trade_date.strftime("%d%m%Y")
        url = f"{ARCHIVES_URL}/archives/nsccl/volt/FOVOLT_{date_str}.csv"

        resp = self.session.get(url)
        if resp.status_code == 200:
            try:
                df = pd.read_csv(io.BytesIO(resp.content), low_memory=False)
                df.columns = [c.strip() for c in df.columns]
                return df
            except Exception as e:
                logger.error(f"Error parsing FO Volatility: {e}")
        return pd.DataFrame()
