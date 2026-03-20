from ingest.date_utils import parse_nse_date
from datetime import datetime

# Test our timestamp format
d = "03-Mar-2025 18:07:08"
# parse_nse_date returns date(), let's see if it handles space
print(parse_nse_date(d))
