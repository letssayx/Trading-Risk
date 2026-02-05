from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, date

# Import Domain & Orchestration
from domain.market.snapshot import MarketSnapshot, InstrumentSnapshot
from domain.instruments.asset import UnderlyingAsset
from domain.instruments.option import OptionContract, OptionType, OptionStyle
from web.auth.routes import router as auth_router
from web.chat.routes import router as chat_router
from web.charts.routes import router as charts_router
from web.risk.routes import router as risk_router
from web.export.routes import router as export_router
from web.ingest.routes import router as ingest_router
from web.dashboard.routes import router as dashboard_router
from web.ui.routes import router as ui_router
from web.widgets.routes import router as widgets_router

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
