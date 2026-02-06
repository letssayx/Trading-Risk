from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
from backend.auth.routes import get_current_user
from backend.domain.common.user import User

router = APIRouter(prefix="/api/strategies", tags=["Strategy Persistence"])

# Mock Database
STRATEGIES_DB = []

class StrategySaveRequest(BaseModel):
    name: str
    code: str
    config: Dict[str, Any]

class StrategyResponse(StrategySaveRequest):
    id: int
    version: int

@router.post("/save", response_model=StrategyResponse)
async def save_strategy(strategy: StrategySaveRequest, current_user: User = Depends(get_current_user)):
    """
    Saves a new version of a strategy.
    """
    new_id = len(STRATEGIES_DB) + 1
    entry = {
        "id": new_id,
        "name": strategy.name,
        "code": strategy.code,
        "config": strategy.config,
        "version": 1, # Increment logic in real DB
        "author": current_user.username
    }
    STRATEGIES_DB.append(entry)
    return entry

@router.get("/list", response_model=List[StrategyResponse])
async def list_strategies(current_user: User = Depends(get_current_user)):
    return STRATEGIES_DB

@router.post("/clone/{strategy_id}")
async def clone_strategy(strategy_id: int, current_user: User = Depends(get_current_user)):
    """
    Clones an existing strategy for a new instrument or tweak.
    """
    # Find strategy
    original = next((s for s in STRATEGIES_DB if s["id"] == strategy_id), None)
    if not original:
        raise HTTPException(status_code=404, detail="Strategy not found")

    new_id = len(STRATEGIES_DB) + 1
    clone = original.copy()
    clone["id"] = new_id
    clone["name"] = f"{original['name']} (Clone)"
    clone["author"] = current_user.username
    STRATEGIES_DB.append(clone)

    return clone
