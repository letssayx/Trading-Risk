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

app = FastAPI(title="Derivatives Analysis System")
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(charts_router)
