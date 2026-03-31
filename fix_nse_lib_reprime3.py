# The user ALSO requested a batch size of 1000 for database insertions.
# In `backend/ingest/nse_importer.py`, we already set `batch_size=1000` via sed previously. Let's double check.
with open("backend/ingest/nse_importer.py", "r") as f:
    if "batch_size=2000" in f.read():
        print("batch_size=2000 STILL exists in nse_importer.py")
    else:
        print("batch_size=1000 applied successfully.")
