import re

with open("backend/ingest/field_mapper.py", "r") as f:
    code = f.read()

# Make sure we don't duplicate patches if it's already there
if "logger.error(f\"Error mapping contract delta: {e}\")" not in code:
    code = code.replace("            if record['symbol'] and record['symbol'].lower() != 'nan':\n                records.append(record)\n        return records", "            if record['symbol'] and record['symbol'].lower() != 'nan':\n                records.append(record)\n        \n        if not records:\n            logger.error(f\"Contract delta mapping produced 0 records from {len(df)} rows. Columns: {df.columns.tolist()}\")\n        return records")

with open("backend/ingest/field_mapper.py", "w") as f:
    f.write(code)
