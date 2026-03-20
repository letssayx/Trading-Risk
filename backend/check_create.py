from infrastructure.db import engine
from ingest.nse_models import Base
Base.metadata.create_all(bind=engine)
print("done")
