from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.jules.ai_assistant import JulesAssistant
import os

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# Global instance
jules_instance = JulesAssistant()

@router.post("/api/jules/chat", response_model=ChatResponse)
async def chat_with_jules(req: ChatRequest):
    # Try using the global instance directly
    # The instance's ask method now handles re-initialization checks
    try:
        resp = await jules_instance.ask(req.message)
        return ChatResponse(response=resp)
    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")
