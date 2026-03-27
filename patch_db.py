with open("backend/infrastructure/db.py", "r") as f:
    content = f.read()
content = content.replace("postgresql+psycopg2://postgres:postgres@db:5432/turtle_terminal", "sqlite:///:memory:?check_same_thread=False")
content = content.replace("pool_size=20,", "")
content = content.replace("max_overflow=10,", "")
content = content.replace("pool_timeout=30,", "")
content = content.replace("pool_recycle=1800", "")
with open("backend/infrastructure/db.py", "w") as f:
    f.write(content)
