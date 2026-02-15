from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.jules.ai_assistant import JulesAssistant
from backend.jules.executor import CodeExecutor

router = APIRouter(prefix="/api/jules", tags=["Jules AI"])

class ParseRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None

class ExecuteRequest(BaseModel):
    code: str
    symbol: str = "NIFTY"

@router.post("/parse")
async def parse_strategy(request: ParseRequest):
    """
    Convert natural language to strategy config/code using Jules AI Assistant.
    Falls back to deterministic parser if LLM keys are missing.
    """
    try:
        assistant = JulesAssistant()

        # Use the Assistant to generate both code and visualization config
        result = assistant.generate_strategy(request.text)

        return {
            "code": result["code"],
            "config": result["config"],
            "message": "Strategy generated successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_assistant(request: ParseRequest):
    """
    General purpose query to Jules Assistant.
    """
    try:
        assistant = JulesAssistant()
        response = assistant.query(request.text, context=request.context)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_strategy(request: ExecuteRequest):
    """Run generated strategy"""
    executor = CodeExecutor()

    # Mock Market Data for Context
    # In prod, fetch from Data Loader
    context = {
        "symbol": request.symbol,
        "data": {"price": 22500, "volatility": 15.5}
    }

    result = executor.execute(request.code, context=context)
    return result
