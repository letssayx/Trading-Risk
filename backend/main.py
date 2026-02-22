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
from backend.web.api.data import upload_routes
from backend.web.api import analysis_routes
from backend.web.api import jules_routes
from backend.web.api import config_routes
from backend.web.api.data import view_routes
from backend.web.api import nse_routes

# Import DB and Models for Initialization
from backend.infrastructure.db import engine, Base
from backend.domain.market.models import Bhavcopy
from backend.ingest import nse_models # Ensure tables are created
from backend.ingest.tasks import setup_timescale_policies
from backend.ingest.tick_vault import TickVault

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
app.include_router(analysis_routes.router)
app.include_router(jules_routes.router)
app.include_router(config_routes.router)
app.include_router(view_routes.router)
app.include_router(nse_routes.router, prefix="/api/v1/nse", tags=["nse"])

@app.on_event("startup")
async def startup_event():
    # Initialize DB
    print("Initializing Database...")
    Base.metadata.create_all(bind=engine)
    try:
        TickVault().init_db()
        print("✅ TickVault initialized")
    except Exception as e:
        print(f"⚠️ TickVault Init Warning: {e}")

    # Trigger TimescaleDB setup (async)
    # Wrap in broad exception handler to prevent startup crash if Broker/DB is down
    try:
        setup_timescale_policies.delay()
        print("✅ TimescaleDB setup triggered")
    except Exception as e:
        # Log error but don't stop startup
        print(f"⚠️ TimescaleDB Setup Warning (Broker/DB may be offline): {e}")

    print("✅ Database initialized")

    # Start log generator (Disabled per user request)
    # asyncio.create_task(logs.log_generator())
    # Start simulated market data (Disabled, now relying on TickVault/DB)
    # asyncio.create_task(live_routes.simulate_market_data())

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

@app.get("/data-viewer")
async def get_data_viewer():
    return FileResponse("backend/ui/templates/data_viewer.html")
