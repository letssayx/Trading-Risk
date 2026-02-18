from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio

# Existing routes
from backend.web import routes
from backend.web.portfolio import routes as portfolio_routes
from backend.web.live import logs
from backend.web.widgets import routes as widget_routes

# New routes
from backend.web.data import routes as data_routes
from backend.web.live import routes as live_routes
from backend.web.strategies import adapters_routes
from backend.web.api.data import upload_routes, view_routes
from backend.web.api import config_routes
from backend.web.api.jules import routes as jules_routes

# Import DB and Models for Initialization
from backend.infrastructure.db import engine, Base
from backend.domain.market import models

app = FastAPI(title="Turtle Terminal - Institutional Shell")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/ui/static"), name="static")

# Include Routers
app.include_router(routes.router)
app.include_router(portfolio_routes.router)
app.include_router(logs.router)
app.include_router(widget_routes.router)
app.include_router(data_routes.router)
app.include_router(live_routes.router)
app.include_router(adapters_routes.router)
app.include_router(upload_routes.router)
app.include_router(config_routes.router)
app.include_router(view_routes.router)
app.include_router(jules_routes.router)

@app.on_event("startup")
async def startup_event():
    # Initialize DB
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✅ PostgreSQL database initialized")

    # Start log generator
    asyncio.create_task(logs.log_generator())
    # Start simulated market data
    asyncio.create_task(live_routes.simulate_market_data())

@app.get("/")
def read_root():
    return {"status": "Turtle Terminal Active"}

@app.get("/spread-builder")
async def get_spread_builder():
    return FileResponse("backend/ui/templates/spread_builder.html")

@app.get("/workbench")
async def get_workbench():
    return FileResponse("backend/ui/templates/workbench.html")

@app.get("/strategy-composer")
async def get_strategy_composer():
    return FileResponse("backend/ui/templates/strategy_composer.html")
