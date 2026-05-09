from backend.ingest.nse_importer import NSEDataImporter
import datetime
import logging
logging.basicConfig(level=logging.DEBUG)

importer = NSEDataImporter()
# Now we import a date which is today to capture the HDFCAMC meeting on 16-Apr-2026 if it was updated
importer.import_date(datetime.date(2026, 4, 16), patterns=['board_meetings'], force=True)
