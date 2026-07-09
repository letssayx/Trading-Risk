from backend.infrastructure.db import engine, Base
from backend.ingest.nse_models import DividendDatabank
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Creating DividendDatabank table...")
    # This will create the table if it does not exist. It will not touch existing tables.
    Base.metadata.create_all(bind=engine, tables=[DividendDatabank.__table__])
    logger.info("DividendDatabank table created successfully.")
