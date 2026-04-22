with open("backend/ingest/nse_models.py", "r") as f:
    text = f.read()

text = text.replace("from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, DateTime, Text, Index, UniqueConstraint, PrimaryKeyConstraint, func, text", "from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, DateTime, Text, Index, UniqueConstraint, PrimaryKeyConstraint, func, text, JSON")

with open("backend/ingest/nse_models.py", "w") as f:
    f.write(text)
