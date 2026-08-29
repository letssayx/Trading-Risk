import datetime
from sqlalchemy import func
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import DividendDatabank
from backend.ingest.tasks import NseTasks

def check():
    print("Testing deduplication")

check()
