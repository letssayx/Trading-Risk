import re

with open('backend/ingest/nse_models.py', 'r') as f:
    text = f.read()

# I need to add total_eq_volume and delivery_pct to DailyDerivativesAnalysis
if "total_eq_volume" not in text:
    search = """    vwap = Column(Float, nullable=True)"""
    replace = """    vwap = Column(Float, nullable=True)
    total_eq_volume = Column(BigInteger, nullable=True)
    delivery_pct = Column(Float, nullable=True)"""
    text = text.replace(search, replace)
    with open('backend/ingest/nse_models.py', 'w') as f:
        f.write(text)
    print("Added columns to model.")
else:
    print("Columns already in model.")
