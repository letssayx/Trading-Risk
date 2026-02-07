import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from backend.domain.market.models import Instrument, MarketData
import uuid

class DataVault:
    """
    Institutional Data Ingestion Service.
    Handles bulk CSV uploads, ticker mapping, and TimescaleDB storage.
    """
    def __init__(self, db: Session):
        self.db = db

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

    def process_csv(self, file_content: bytes):
        """
        Parses CSV and inserts into MarketData hypertable.
        Expected Cols: ticker, timestamp, open, high, low, close, volume, iv (optional)
        """
        # Ensure it's treated as bytes
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')

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
                ts = pd.to_datetime(row.get('timestamp') or row.get('date'))
                if ts.tzinfo is None:
                    ts = ts.tz_localize('UTC') # Default to UTC if naive

                market_data = MarketData(
                    time=ts,
                    turtle_id=instrument.turtle_id,
                    open=row.get('open', 0),
                    high=row.get('high', 0),
                    low=row.get('low', 0),
                    close=row.get('close', 0),
                    volume=row.get('volume', 0),
                    iv=row.get('iv', 0),
                    greeks=row.get('greeks', {}) # Assuming JSON or dict if present
                )
                self.db.add(market_data)
                records_processed += 1
            except Exception as e:
                print(f"Skipping row for {ticker}: {e}")
                continue

        self.db.commit()
        return records_processed
