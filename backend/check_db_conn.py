import asyncio
from infrastructure.db import get_db, SessionLocal
from ingest.nse_models import BoardMeeting

def main():
    db = SessionLocal()
    print("DB connection successful.")

if __name__ == "__main__":
    main()
