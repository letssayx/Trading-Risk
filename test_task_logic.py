import pytest
from backend.ingest.tasks import build_dividend_databank_task

def test_syntax():
    assert build_dividend_databank_task is not None
