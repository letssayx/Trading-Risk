import re

with open('backend/ingest/nse_models.py', 'r') as f:
    content = f.read()

# BoardMeeting
content = content.replace("UniqueConstraint('date', 'symbol', 'purpose', name='uq_board_meeting_unique'),", "UniqueConstraint('date', 'symbol', name='uq_board_meeting_unique'),")

# CorporateAction
content = content.replace("UniqueConstraint('date', 'symbol', 'purpose', name='uq_corporate_action_unique'),", "UniqueConstraint('date', 'symbol', name='uq_corporate_action_unique'),")

with open('backend/ingest/nse_models.py', 'w') as f:
    f.write(content)

print("Updated unique constraints in nse_models.py")
