import datetime
import os
import sys

# Ensure clock is set to 2026-07-19 per memory directives.
# We'll mock datetime if needed, or simply run the extract_amount_from_pdf function directly.

from backend.ingest.parse_pdf import extract_amount_from_pdf

def test():
    # Bharti Airtel outcome PDF link (example, we don't know the exact one but we can try some standard parsing testing)
    url = "https://nsearchives.nseindia.com/corporate/BHARTIARTL_10072026130420_BhartiAirtelLimited_Outcome.pdf"

    # We will test extract_amount_from_pdf just by executing it to ensure it compiles/runs.
    pass

if __name__ == "__main__":
    test()
