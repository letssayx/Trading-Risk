from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from backend.infrastructure.db import get_db
from backend.ingest.nse_models import PreMarketSnapshot, EconomicEvent
from backend.ingest.macro.fetcher import MacroDataFetcher
import json

router = APIRouter()

@router.post("/api/macro/sync")
def sync_macro_data(db: Session = Depends(get_db)):
    """Fetches real-time macro data and events and stores them in the DB."""
    try:
        today = datetime.now().date()

        # 1. Fetch Market Snapshot
        snapshot_data = MacroDataFetcher.build_snapshot()

        # Upsert Snapshot
        existing_snapshot = db.query(PreMarketSnapshot).filter(PreMarketSnapshot.trade_date == today).first()
        if existing_snapshot:
            existing_snapshot.snapshot_data = snapshot_data
        else:
            new_snapshot = PreMarketSnapshot(trade_date=today, snapshot_data=snapshot_data)
            db.add(new_snapshot)

        # 2. Fetch Events
        events_data = MacroDataFetcher.get_economic_events()

        # Clear today's previously stored future events and rewrite them to keep them fresh
        db.query(EconomicEvent).filter(EconomicEvent.trade_date == today).delete()

        for e in events_data:
            try:
                # Naive parse, ForexFactory XML format is usually '%m-%d-%Y %I:%M%p'
                dt_str = e['event_date']
                try:
                    event_dt = datetime.strptime(dt_str, "%m-%d-%Y %I:%M%p")
                except:
                    event_dt = datetime.now() # Fallback
            except:
                 event_dt = datetime.now()

            db.add(EconomicEvent(
                trade_date=today,
                event_date=event_dt,
                country=e['country'],
                event_name=e['event_name'],
                actual=e.get('actual', ''),
                forecast=e.get('forecast', ''),
                previous=e.get('previous', ''),
                impact=e['impact']
            ))

        db.commit()
        return {"status": "success", "message": "Macro data synced successfully", "date": str(today)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/macro/data")
def get_macro_data(target_date: str = None, db: Session = Depends(get_db)):
    """Returns the macro snapshot and events for a given date (defaults to latest)."""
    try:
        if target_date:
            target = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            # Get latest available date
            latest = db.query(PreMarketSnapshot).order_by(PreMarketSnapshot.trade_date.desc()).first()
            if not latest:
                return {"snapshot": {}, "events": [], "date": None}
            target = latest.trade_date

        snapshot = db.query(PreMarketSnapshot).filter(PreMarketSnapshot.trade_date == target).first()
        events = db.query(EconomicEvent).filter(EconomicEvent.trade_date == target).order_by(EconomicEvent.event_date.asc()).all()

        return {
            "date": str(target),
            "snapshot": snapshot.snapshot_data if snapshot else {},
            "events": [
                {
                    "date": e.event_date.strftime("%Y-%m-%d %H:%M") if e.event_date else "",
                    "country": e.country,
                    "event": e.event_name,
                    "actual": e.actual,
                    "forecast": e.forecast,
                    "previous": e.previous,
                    "impact": e.impact
                } for e in events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
