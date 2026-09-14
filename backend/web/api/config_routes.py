from fastapi import APIRouter, Depends
from pydantic import BaseModel
import os
from backend.dependencies import require_admin

router = APIRouter()

class ConfigUpdate(BaseModel):
    google_api_key: str = None
    groq_api_key: str = None
    openrouter_api_key: str = None

@router.get("/api/config", dependencies=[Depends(require_admin)])
async def get_config():
    # Return masked keys or just status
    return {
        "google_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY"))
    }

@router.post("/api/config", dependencies=[Depends(require_admin)])
async def update_config(config: ConfigUpdate):
    try:
        from dotenv import set_key
        dotenv_path = ".env"
        # Ensure .env file exists
        if not os.path.exists(dotenv_path):
            open(dotenv_path, "a").close()

        if config.google_api_key:
            os.environ["GOOGLE_API_KEY"] = config.google_api_key
            set_key(dotenv_path, "GOOGLE_API_KEY", config.google_api_key)
        if config.groq_api_key:
            os.environ["GROQ_API_KEY"] = config.groq_api_key
            set_key(dotenv_path, "GROQ_API_KEY", config.groq_api_key)
        if config.openrouter_api_key:
            os.environ["OPENROUTER_API_KEY"] = config.openrouter_api_key
            set_key(dotenv_path, "OPENROUTER_API_KEY", config.openrouter_api_key)
    except ImportError:
        # Fallback if python-dotenv isn't installed for some reason
        if config.google_api_key:
            os.environ["GOOGLE_API_KEY"] = config.google_api_key
        if config.groq_api_key:
            os.environ["GROQ_API_KEY"] = config.groq_api_key
        if config.openrouter_api_key:
            os.environ["OPENROUTER_API_KEY"] = config.openrouter_api_key

    return {"status": "Config updated and persisted"}
