from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from dotenv import set_key, load_dotenv

router = APIRouter()

class ApiKeyUpdate(BaseModel):
    provider: str  # 'google' or 'groq'
    key: str

@router.post("/api/config/update-key")
async def update_api_key(req: ApiKeyUpdate):
    """
    Update API Key in .env file
    """
    env_file = ".env"

    # Map provider to env var name
    key_map = {
        "google": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY"
    }

    if req.provider not in key_map:
        raise HTTPException(400, "Invalid provider")

    env_var = key_map[req.provider]

    try:
        # Update .env file
        if not os.path.exists(env_file):
            with open(env_file, 'w') as f:
                f.write("")

        set_key(env_file, env_var, req.key)

        # Reload env vars in current process
        os.environ[env_var] = req.key

        return {"success": True, "message": f"{req.provider} API Key updated"}

    except Exception as e:
        raise HTTPException(500, f"Failed to update key: {str(e)}")
