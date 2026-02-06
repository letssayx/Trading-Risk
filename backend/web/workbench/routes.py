from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import uuid
import os

from backend.dependencies import get_db
from backend.auth.routes import get_current_user
from backend.domain.common.user import User
from backend.strategies.models import Strategy
from backend.domain.audit.models import AuditTrail
from backend.registry.manager import PluginManager

router = APIRouter(prefix="/workbench", tags=["Workbench"])
plugin_manager = PluginManager()

@router.get("/state")
async def get_workbench_state(db: Session = Depends(get_db)):
    """
    Returns the active dashboard layout and registry status.
    """
    strategies = db.query(Strategy).all()

    registry_view = []
    for s in strategies:
        # Check if actually loaded in memory
        status = "Active" if s.is_active else "Inactive"
        if s.is_active and not plugin_manager.get_active_instance(str(s.id)):
             # Try to load if marked active but missing
             try:
                 plugin_manager.register_from_db(s)
                 status = "Active"
             except Exception:
                 status = "Error"

        registry_view.append({
            "id": str(s.id),
            "name": s.name,
            "type": s.type,
            "is_active": s.is_active,
            "status": status,
            "config": s.config_json,
            "version": s.version,
            "source_code": s.source_code
        })

    # Get recent audit logs
    logs = db.query(AuditTrail).order_by(AuditTrail.timestamp.desc()).limit(50).all()

    return {
        "registry": registry_view,
        "audit_feed": [l.to_dict() for l in logs]
    }

@router.post("/strategies/tweak")
async def tweak_strategy_config(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates config_json, logs to AuditTrail, and triggers Hot-Reload.
    Payload: {"strategy_id": "...", "config": {...}}
    """
    strat_id = payload.get("strategy_id")
    new_config = payload.get("config")

    strategy = db.query(Strategy).filter(Strategy.id == strat_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # 1. Capture Before State
    before_state = strategy.config_json

    # 2. Update DB
    strategy.config_json = new_config
    strategy.version += 1
    db.commit()
    db.refresh(strategy)

    # 3. Log Audit
    audit_entry = AuditTrail(
        user_id=current_user.id,
        action_type="TWEAK_PARAM",
        entity_type=strategy.type,
        entity_id=str(strategy.id),
        before_state=before_state,
        after_state=new_config
    )
    db.add(audit_entry)
    db.commit()

    # 4. Hot Reload
    if strategy.is_active:
        try:
            plugin_manager.reload_plugin(strategy)
        except Exception as e:
            return {"status": "Updated DB but Reload Failed", "error": str(e)}

    return {"status": "Success", "new_version": strategy.version}

@router.get("/market/search")
async def market_search(q: str, db: Session = Depends(get_db)):
    """
    Fuzzy search for instruments.
    """
    # Mock implementation until Instrument table is populated or full-text search is set up
    # In prod: db.query(Instrument).filter(Instrument.ticker.ilike(f"%{q}%")).all()
    results = []
    mock_db = ["NIFTY", "BANKNIFTY", "RELIANCE", "HDFCBANK", "INFY"]
    for m in mock_db:
        if q.lower() in m.lower():
            results.append({"ticker": m, "name": f"{m} Futures"})
    return results
