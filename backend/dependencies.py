import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables (including DATABASE_URL) from .env if present.
# We *do not* swallow errors here – if .env is malformed or unreadable, that
# should surface and fail fast rather than silently falling back.
load_dotenv()

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or DATABASE_URL == "postgresql://user:pass@localhost:5432/db":
    raise RuntimeError(
        "DATABASE_URL is not set or is still using the placeholder "
        "'postgresql://user:pass@localhost:5432/db'. "
        "Configure a real DATABASE_URL in your environment or .env file."
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user():
    # Mock user for now as Auth middleware might be missing or complex
    return {"id": "user_123", "username": "trader"}
