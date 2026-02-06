from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, date

# Import Domain & Orchestration
from backend.domain.market.snapshot import MarketSnapshot, InstrumentSnapshot
from backend.domain.instruments.asset import UnderlyingAsset
from backend.domain.instruments.option import OptionContract, OptionType, OptionStyle
from backend.auth.routes import router as auth_router
from backend.chat.routes import router as chat_router
from backend.charts.routes import router as charts_router
from backend.risk.routes import router as risk_router
from backend.export.routes import router as export_router
from backend.ingest.routes import router as ingest_router
from backend.dashboard.routes import router as dashboard_router
from backend.ui.routes import router as ui_router
from backend.widgets.routes import router as widgets_router
from backend.web.search.routes import router as search_router
from backend.web.strategies.routes import router as strategies_router
from backend.web.workbench.routes import router as workbench_router
from backend.web.live.routes import router as live_router

app = FastAPI(title="Derivatives Analysis System")
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(charts_router)
app.include_router(risk_router)
app.include_router(export_router)
app.include_router(ingest_router)
app.include_router(dashboard_router)
app.include_router(ui_router)
app.include_router(widgets_router)
app.include_router(search_router)
app.include_router(strategies_router)
app.include_router(workbench_router)
app.include_router(live_router)
