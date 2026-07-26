from datetime import date, datetime
from backend.ingest.nse_lib import NSELib
import pandas as pd

nselib = NSELib()

# Simulate importing exactly on 22-Jul-2026 when COALINDIA record date and AGM was announced.
# But wait, it's not a BM, it's just a general update.
# Where is this captured?

df_ca = nselib.get_corporate_actions(date(2026, 7, 24))
print(df_ca[df_ca['SYMBOL'] == 'COALINDIA'])
