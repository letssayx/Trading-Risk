from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment variable
# Default to postgresql local dev if not set
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jules@localhost/turtle_terminal")

# Add standard connection pooling settings to prevent blocking
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Allow 20 concurrent connections
    max_overflow=10,       # Allow 10 extra temporary connections during bursts
    pool_timeout=30,       # Time out and drop requests if a connection isn't available after 30s
    pool_recycle=1800      # Recycle connections after 30 minutes to prevent stale backend states
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Configure DB Logging globally for sqlalchemy to prevent query puking
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
