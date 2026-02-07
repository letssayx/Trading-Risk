from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.core.portfolio.trade_logger import TradeRecord
from backend.core.risk.scorecard import StrategyScorecard

router = APIRouter(prefix="/performance", tags=["Performance"])

@router.get("/report/{strategy_id}")
async def get_strategy_report(strategy_id: str, db: Session = Depends(get_db)):
    """
    Generates Scorecard for a Strategy.
    """
    trades = db.query(TradeRecord).filter(
        TradeRecord.strategy_id == strategy_id,
        TradeRecord.status == "CLOSED"
    ).all()

    trade_dicts = [{"pnl": t.pnl} for t in trades]

    # Mock Historical Target (In prod, fetch from Strategy model or Config)
    target_win_rate = 60.0

    scorecard = StrategyScorecard(historical_win_rate=target_win_rate)
    result = scorecard.evaluate(trade_dicts)

    return result
