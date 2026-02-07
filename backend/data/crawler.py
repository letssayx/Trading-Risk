import requests
import time
import os
from datetime import date
from sqlalchemy.orm import Session
from backend.data.patterns import DatePatternManager
from backend.ingest.data_vault import DataVault

class MarketCrawler:
    """
    Automated NSE Data Fetcher with Retry Logic.
    """
    def __init__(self, db: Session):
        self.db = db
        self.vault = DataVault(db)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_file(self, file_type: str, target_date: date, retries: int = 3):
        url = DatePatternManager.get_url(file_type, target_date)
        if not url:
            print(f"No URL pattern for {file_type}")
            return False

        print(f"Fetching {file_type} from {url}...")

        for attempt in range(retries):
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                if resp.status_code == 200:
                    content = resp.content

                    # Store & Parse
                    file_name = url.split("/")[-1]
                    # If ZIP, unzip (Mock logic for now, DataVault handles bytes)
                    # For MTO (DAT file), treat as CSV

                    self.vault.process_csv(content, file_name=file_name)
                    print(f"✅ Synced {file_type}")
                    return True
                elif resp.status_code == 404:
                    print(f"❌ 404 Not Found (Holiday?): {url}")
                    break # Don't retry 404
                else:
                    print(f"⚠️ Error {resp.status_code}. Retrying...")
                    time.sleep(5)
            except Exception as e:
                print(f"⚠️ Connection Error: {e}")
                time.sleep(5)

        return False

    def sync_all(self, target_date: date):
        """
        Orchestrates sync of all 11 critical files.
        """
        files = ["MTO", "BHAVCOPY_FO", "PARTICIPANT_OI"]
        results = {}
        for f in files:
            results[f] = self.fetch_file(f, target_date)
        return results
