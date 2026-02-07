import requests
import pandas as pd
import io
import zipfile
from datetime import datetime, date
from sqlalchemy.orm import Session
from backend.domain.market.participant import ParticipantPosition
from backend.domain.market.models import MarketData
from backend.ingest.data_vault import DataVault

class NSEIngestionService:
    """
    Automates downloading and parsing of NSE Participant-Wise OI and Bhavcopy.
    """
    def __init__(self, db: Session):
        self.db = db
        self.data_vault = DataVault(db)
        # Mock URLs or Real ones if available. Using placeholders for MVP structure.
        self.participant_oi_url = "https://archives.nseindia.com/content/nsccl/fao_participant_oi_{date}.csv"
        self.bhavcopy_url = "https://archives.nseindia.com/content/historical/DERIVATIVES/{year}/{month}/fo{date}bhav.csv.zip"

    def download_participant_oi(self, target_date: date):
        """
        Downloads and parses Participant Wise OI CSV.
        Format: Client Type, Future Index Long, Future Index Short, ...
        """
        date_str = target_date.strftime("%d%m%Y")
        url = self.participant_oi_url.format(date=date_str)

        try:
            # Mocking Request for MVP Determinism
            # resp = requests.get(url)
            # content = resp.content
            # Simulating content for logic verification
            content = b"""Client Type,Future Index Long,Future Index Short,Option Index Call Long,Option Index Call Short
FII,15000,12000,50000,45000
DII,8000,15000,2000,5000
PRO,12000,12000,30000,35000
CLIENT,40000,35000,80000,75000
"""
            df = pd.read_csv(io.BytesIO(content))
            self._store_participant_oi(df, target_date)
            return True
        except Exception as e:
            print(f"Failed to download Participant OI: {e}")
            return False

    def _store_participant_oi(self, df: pd.DataFrame, timestamp: date):
        for _, row in df.iterrows():
            ptype = row['Client Type']

            # Index Futures
            f_long = int(row.get('Future Index Long', 0))
            f_short = int(row.get('Future Index Short', 0))

            rec = ParticipantPosition(
                time=timestamp,
                participant_type=ptype,
                instrument_type="INDEX_FUT",
                long_contracts=f_long,
                short_contracts=f_short,
                net_contracts=f_long - f_short
            )
            self.db.merge(rec) # Upsert

        self.db.commit()

    def download_bhavcopy(self, target_date: date):
        """
        Downloads Daily Bhavcopy ZIP, extracts CSV, and feeds DataVault.
        """
        # Mock Logic for MVP
        print(f"Downloading Bhavcopy for {target_date}...")
        # 1. Download ZIP
        # 2. Extract CSV
        # 3. DataVault.process_csv(csv_content)
        pass
