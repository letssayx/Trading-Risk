from fastapi import APIRouter
from pydantic import BaseModel
from backend.jules.ai_assistant import jules

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/api/jules/chat")
async def chat(req: ChatRequest):
    response = await jules.get_response(req.message)
    return {"reply": response}

@router.post("/api/jules/command")
async def command(req: ChatRequest):
    response = await jules.get_response(f"Execute command: {req.message}")
    return {"reply": response}
