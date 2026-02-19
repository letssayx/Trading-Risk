from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import set_key

router = APIRouter()

class ApiKeyUpdate(BaseModel):
    provider: str  # 'google', 'groq', 'upstox'
    key: str
    secret: Optional[str] = None

@router.post("/api/config/update-key")
async def update_api_key(req: ApiKeyUpdate):
    """
    Update API Key in .env file
    """
    env_file = ".env"

    # Map provider to env var name
    key_map = {
        "google": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY",
        "upstox": "UPSTOX_ACCESS_TOKEN" # Treating key input as Access Token for Upstox
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
        os.environ[env_var] = req.key

        # Handle Secret if provided (e.g. for Upstox)
        if req.provider == "upstox" and req.secret:
             set_key(env_file, "UPSTOX_API_SECRET", req.secret)
             os.environ["UPSTOX_API_SECRET"] = req.secret

        return {"success": True, "message": f"{req.provider} API Key updated"}

    except Exception as e:
        raise HTTPException(500, f"Failed to update key: {str(e)}")
