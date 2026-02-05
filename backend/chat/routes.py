from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.orchestration.pipelines.executor import Executor
from backend.auth.routes import get_current_user
from backend.domain.common.user import User
from backend.dependencies import get_executor

router = APIRouter(prefix="/api", tags=["Chat"])

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    result: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    executor: Executor = Depends(get_executor)
):
    """
    Handles user queries, invokes Gemini (via Executor), and executes deterministic logic.
    """
    # Execute query
    result_text = executor.execute_query(current_user.id, request.query)

    return ChatResponse(result=result_text)
