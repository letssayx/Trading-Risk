import re
with open('alembic/versions/create_highest_oi_cols.py', 'r') as f:
    content = f.read()

revision_match = re.search(r"revision\s*=\s*'([^']+)'", content)
print("Actual revision of create_highest_oi_cols:", revision_match.group(1))
