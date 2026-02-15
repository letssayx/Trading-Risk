import os
from pathlib import Path

# Try to load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

class Settings:
    PROJECT_NAME: str = "Turtle Terminal"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENV: str = os.getenv("ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://turtle_user:turtle_pass@localhost:5432/turtle_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Upstox Integration
    UPSTOX_API_KEY: str = os.getenv("UPSTOX_API_KEY", "")
    UPSTOX_API_SECRET: str = os.getenv("UPSTOX_API_SECRET", "")
    UPSTOX_REDIRECT_URI: str = os.getenv("UPSTOX_REDIRECT_URI", "http://localhost:8000/auth/callback")

    # AI / LLM
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Market Data
    MARKET_DATA_PROVIDER: str = os.getenv("MARKET_DATA_PROVIDER", "mock")  # mock, upstox, nse

settings = Settings()
