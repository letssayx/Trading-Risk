import pytest
from datetime import date
from backend.ingest.tasks import build_dividend_databank_task
from backend.infrastructure.db import SessionLocal

def test_task():
    print("Task compiled successfully!")
