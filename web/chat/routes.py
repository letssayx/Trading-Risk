from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from orchestration.pipelines.executor import Executor
from web.auth.routes import get_current_user
from domain.common.user import User
from web.dependencies import get_executor

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
