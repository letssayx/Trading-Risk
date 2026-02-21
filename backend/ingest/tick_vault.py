from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from backend.infrastructure.db import engine

class TickVault:
    """
    Manages high-frequency tick data storage using PostgreSQL (TimeSeries style).
    If TimescaleDB extension is available, it should use hypertables.
    """
    def __init__(self):
        # We use the global engine
        pass

    def init_db(self):
        """
        Create ticks table if not exists.
        Ideally this is a migration.
        """
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ticks (
                    time TIMESTAMPTZ NOT NULL,
                    symbol TEXT NOT NULL,
                    price DOUBLE PRECISION,
                    volume INTEGER,
                    oi INTEGER
                );
            """))
            # Try to convert to hypertable if timescale exists (ignore error if not)
            try:
                conn.execute(text("SELECT create_hypertable('ticks', 'time', if_not_exists => TRUE);"))
            except Exception:
                pass # Timescale not installed/enabled
            conn.commit()

    def store_tick(self, tick: Dict[str, Any]):
        """
        Persists a single tick.
        tick = {symbol, price, volume, oi, timestamp}
        """
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO ticks (time, symbol, price, volume, oi)
                VALUES (:timestamp, :symbol, :price, :volume, :oi)
            """), tick)
            conn.commit()

    def fetch_history(self, symbol: str, limit=100) -> List[Dict]:
        """
        Fetch last N ticks
        """
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT time, price, volume, oi
                FROM ticks
                WHERE symbol = :symbol
                ORDER BY time DESC
                LIMIT :limit
            """), {"symbol": symbol, "limit": limit})

            return [
                {"time": row[0].isoformat(), "price": row[1], "volume": row[2], "oi": row[3]}
                for row in result
            ]
