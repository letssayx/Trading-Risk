import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from backend.domain.market.models import Instrument, MarketData
from backend.domain.ingest.audit import IngestionAudit
import uuid
import hashlib

class DataVault:
    """
    Institutional Data Ingestion Service.
    Handles bulk CSV uploads, ticker mapping, and TimescaleDB storage.
    """
    def __init__(self, db: Session):
        self.db = db

    def calculate_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def is_duplicate(self, file_name: str, content: bytes) -> bool:
        """
        Idempotency Check: Returns True if file hash already processed.
        """
        f_hash = self.calculate_hash(content)
        exists = self.db.query(IngestionAudit).filter(IngestionAudit.file_hash == f_hash).first()
        return exists is not None

    def log_ingestion(self, file_name: str, content: bytes, record_count: int, status: str = "SUCCESS"):
        f_hash = self.calculate_hash(content)
        audit = IngestionAudit(
            file_name=file_name,
            file_hash=f_hash,
            file_type="GENERIC_CSV",
            status=status,
            record_count=record_count
        )
        self.db.add(audit)
        self.db.commit()

    def get_or_create_instrument(self, ticker: str, exchange: str = "NSE") -> Instrument:
        """
        Maps vendor ticker to internal turtle_id.
        """
        inst = self.db.query(Instrument).filter(
            Instrument.ticker == ticker,
            Instrument.exchange == exchange
        ).first()

        if not inst:
            # Create new registry entry
            inst = Instrument(
                turtle_id=uuid.uuid4(),
                ticker=ticker,
                exchange=exchange,
                name=f"{ticker} Auto-Gen",
                asset_class="Unknown" # Default, can be updated later
            )
            self.db.add(inst)
            self.db.commit()
            self.db.refresh(inst)

        return inst

    def process_csv(self, file_content: bytes, file_name: str = "manual_upload.csv"):
        """
        Parses CSV and inserts into MarketData hypertable.
        Expected Cols: ticker, timestamp, open, high, low, close, volume, iv (optional)
        """
        # Ensure it's treated as bytes
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')

        # Check Deduplication
        if self.is_duplicate(file_name, file_content):
            print(f"Skipping duplicate file: {file_name}")
            return 0

        df = pd.read_csv(pd.io.common.BytesIO(file_content))

        # Normalize columns
        df.columns = [c.lower().strip() for c in df.columns]

        records_processed = 0

        for _, row in df.iterrows():
            ticker = row.get('ticker') or row.get('symbol')
            if ticker:
                ticker = str(ticker).strip() # Ensure string

            if not ticker: continue

            # Map Ticker
            instrument = self.get_or_create_instrument(ticker)

            # Prepare Data
            try:
                raw_ts = row.get('timestamp') or row.get('date') or datetime.utcnow()
                ts = pd.to_datetime(raw_ts)
                if pd.isna(ts): # Handle NaT
                    ts = datetime.utcnow()
                if ts.tzinfo is None:
                    ts = ts.tz_localize('UTC') # Default to UTC if naive

                # Helper to clean numeric values (NaN to 0)
                def clean_num(val):
                    if pd.isna(val): return 0
                    return val

                market_data = MarketData(
                    time=ts,
                    turtle_id=instrument.turtle_id,
                    open=clean_num(row.get('open')),
                    high=clean_num(row.get('high')),
                    low=clean_num(row.get('low')),
                    close=clean_num(row.get('close')),
                    volume=int(clean_num(row.get('volume'))),
                    iv=clean_num(row.get('iv')),
                    greeks=row.get('greeks', {}) or {} # Assuming JSON or dict if present
                )
                self.db.add(market_data)
                records_processed += 1
            except Exception as e:
                print(f"Skipping row for {ticker}: {e}")
                continue

        self.db.commit()
        self.log_ingestion(file_name, file_content, records_processed)
        return records_processed
