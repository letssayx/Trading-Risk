import os
from dotenv import load_dotenv

# 1. Load the keys from the .env file into the system environment
load_dotenv()

class Config:
    """
    Centralized configuration manager for Turtle Terminal.
    Ensures keys are loaded or raises an error if missing.
    """
    MARKET_DATA_KEY = os.getenv("MARKET_DATA_KEY")
    AI_KEY = os.getenv("AI_ORCHESTRATOR_KEY")
    MODE = os.getenv("SYSTEM_MODE", "DEVELOPMENT")

    @classmethod
    def validate(cls):
        """Checks that all essential keys are present."""
        if not cls.MARKET_DATA_KEY:
            raise EnvironmentError("MISSING: MARKET_DATA_KEY not found in .env")
        if not cls.AI_KEY:
            raise EnvironmentError("MISSING: AI_ORCHESTRATOR_KEY not found in .env")
        print(f"✅ Turtle Terminal Config: {cls.MODE} mode active.")

# Auto-validate on startup
if __name__ == "__main__":
    Config.validate()
