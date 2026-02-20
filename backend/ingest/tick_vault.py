from typing import Dict, List, Any
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import os

class TickVault:
    """
    Manages high-frequency tick data storage using TimescaleDB.
    """
    def __init__(self, connection_string: str = None):
        self.conn_str = connection_string or os.getenv("DATABASE_URL", "postgresql://jules@localhost/turtle_terminal")
        self._init_db()

    def _get_conn(self):
        return psycopg2.connect(self.conn_str)

    def _init_db(self):
        """
        Initialize TimescaleDB hypertable if not exists.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ticks (
            time        TIMESTAMPTZ NOT NULL,
            symbol      TEXT NOT NULL,
            price       DOUBLE PRECISION,
            volume      INTEGER,
            oi          INTEGER
        );
        """
        # Note: We need to enable timescaledb extension first usually, assuming it's done in DB init
        # or checking "SELECT create_hypertable('ticks', 'time', if_not_exists => TRUE);"
        create_hypertable_sql = "SELECT create_hypertable('ticks', 'time', if_not_exists => TRUE);"

        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(create_table_sql)
                    try:
                        cur.execute(create_hypertable_sql)
                    except psycopg2.Error as e:
                        # Might fail if not timescale enabled or already hypertable
                        print(f"Hypertable init warning (might be normal if standard PG): {e}")
                conn.commit()
        except Exception as e:
            print(f"TickVault Init Error: {e}")

    def store_ticks(self, ticks: List[Dict[str, Any]]):
        """
        Persists a batch of ticks.
        ticks: list of dicts with keys: time, symbol, price, volume, oi
        """
        if not ticks:
            return

        sql = "INSERT INTO ticks (time, symbol, price, volume, oi) VALUES %s"
        # Transform dicts to tuples for bulk insert
        values = [(
            t['time'],
            t['symbol'],
            t.get('price'),
            t.get('volume', 0),
            t.get('oi', 0)
        ) for t in ticks]

        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    execute_values(cur, sql, values)
                conn.commit()
        except Exception as e:
            print(f"TickVault Insert Error: {e}")

    def fetch_ticks(self, ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
        """
        Retrieves ticks for a range.
        """
        sql = """
        SELECT time, price, volume, oi
        FROM ticks
        WHERE symbol = %s AND time >= %s AND time <= %s
        ORDER BY time ASC
        """
        try:
            with self._get_conn() as conn:
                df = pd.read_sql(sql, conn, params=(ticker, start, end))
                return df
        except Exception as e:
            print(f"TickVault Fetch Error: {e}")
            return pd.DataFrame()
