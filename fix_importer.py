import re

with open('backend/ingest/nse_importer.py', 'r') as f:
    content = f.read()

# Make fii_dii_cash delete existing records before insert to prevent chunks conflict on double runs
new_content = content.replace("            'bhavcopy_fo': ['trade_date', 'ticker_symb', 'instrument_type', 'expiry_date', 'strike_price', 'option_type'],", "            'bhavcopy_fo': ['trade_date', 'ticker_symb', 'instrument_type', 'expiry_date', 'strike_price', 'option_type'],\n            'fii_dii_cash': [], # Force delete-insert")
new_content = new_content.replace("            'fii_dii_cash': ['trade_date', 'category'],", "")

with open('backend/ingest/nse_importer.py', 'w') as f:
    f.write(new_content)
