from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.jules.strategy_parser import StrategyParser
from backend.jules.executor import CodeExecutor

router = APIRouter(prefix="/api/jules", tags=["Jules AI"])

class ParseRequest(BaseModel):
    text: str

class ExecuteRequest(BaseModel):
    code: str
    symbol: str = "NIFTY"

@router.post("/parse")
async def parse_strategy(request: ParseRequest):
    """Convert natural language to strategy config"""
    try:
        parser = StrategyParser()
        parsed = parser.parse(request.text)
        code = parser.generate_code(parsed)
        return {"code": code, "config": parsed}
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
