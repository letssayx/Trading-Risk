import re

with open('backend/ingest/nse_importer.py', 'r') as f:
    content = f.read()

# We need to change the deduplication logic for board meetings and corporate actions
# so that they just use `date` and `symbol` for uniqueness, effectively only keeping the last one.
# So change:
#            'corporate_actions': ['date', 'symbol', 'purpose'],
#            'board_meetings': ['date', 'symbol', 'purpose'],
# to
#            'corporate_actions': ['date', 'symbol'],
#            'board_meetings': ['date', 'symbol'],

content = content.replace("'corporate_actions': ['date', 'symbol', 'purpose'],", "'corporate_actions': ['date', 'symbol'],")
content = content.replace("'board_meetings': ['date', 'symbol', 'purpose'],", "'board_meetings': ['date', 'symbol'],")

with open('backend/ingest/nse_importer.py', 'w') as f:
    f.write(content)

print("Updated unique fields for deduping.")
