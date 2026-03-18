import re

with open('backend/web/api/data/view_routes.py', 'r') as f:
    text = f.read()

search = """        'fii_dii_cash': models.FIIDIICash,
        'security_master': models.SecurityMaster,"""

replace = """        'fii_dii_cash': models.FIIDIICash,
        'security_master': models.SecurityMaster,
        'historical_index_data': models.HistoricalIndexData,"""

if search in text:
    text = text.replace(search, replace)
    with open('backend/web/api/data/view_routes.py', 'w') as f:
        f.write(text)
    print("Fixed historical_index_data view_routes mapping")
else:
    print("Could not find the search block")
