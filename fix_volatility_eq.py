import re

# NIFTY does not have data in `bhavcopy_eq`!
# It's an index. If the user searches for NIFTY, `bhavcopy_eq` will return empty, and the chart will fail and be empty!
# We must use `bhavcopy_idx` or `bhavcopy_fo` to get index prices in `get_pre_expiry_action`!
