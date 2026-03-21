import re
with open("backend/infrastructure/db.py", "r") as f:
    content = f.read()
# Replace ALL database_url logic to force sqlite
content = re.sub(
    r"DATABASE_URL = os\.getenv\('DATABASE_URL', '.*'\)",
    "DATABASE_URL = 'sqlite:///:memory:?check_same_thread=False'",
    content
)
with open("backend/infrastructure/db.py", "w") as f:
    f.write(content)
