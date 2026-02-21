from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.jules.ai_assistant import JulesAssistant
import os

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# Try to init Jules
try:
    jules = JulesAssistant()
except Exception as e:
    print(f"Jules init failed: {e}")
    jules = None

@router.post("/api/jules/chat", response_model=ChatResponse)
async def chat_with_jules(req: ChatRequest):
    if not jules:
        return ChatResponse(response="Jules is offline (API Key missing).")

    try:
        # Use simple ask for now
        resp = await jules.ask(req.message)
        return ChatResponse(response=resp)
    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")
