from fastapi import APIRouter
from pydantic import BaseModel
# Import the singleton instance directly
from backend.jules.ai_assistant import jules

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/api/jules/chat", response_model=ChatResponse)
async def chat_with_jules(req: ChatRequest):
    if not jules:
        return ChatResponse(response="Jules failed to initialize.")

    try:
        # Use get_response method from new class
        resp = await jules.get_response(req.message)
        return ChatResponse(response=resp)
    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")
