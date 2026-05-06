import sys
import os
sys.path.append('/app/backend')
from datetime import date
from ingest.nse_lib import NSELib
import json

lib = NSELib()
df = lib.get_board_meetings(date(2026, 3, 24))
print("Finished!")
