from backend.infrastructure.db import engine, Base
from backend.ingest import nse_models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
