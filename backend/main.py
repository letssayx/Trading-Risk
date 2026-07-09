from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
from logging.handlers import RotatingFileHandler

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Reduced maxBytes to 5MB and backupCount to 3 to save space
        RotatingFileHandler('nse_import.log', maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)

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
from backend.web.api.data import view_routes, derivatives_routes, special_sit_routes, build_databank
from backend.web.api import nse_routes
from backend.web.api import audit_routes
from backend.web.api import macro_routes
from backend.web.ai.routes import ai_router
from backend.api.v1 import mutual_fund as mutual_fund_routes

# Import DB and Models for Initialization
from backend.infrastructure.db import engine, Base
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
app.include_router(derivatives_routes.router)
app.include_router(special_sit_routes.router)
app.include_router(build_databank.router)
from backend.web.api.data import options_routes, opt_analysis_routes, volatility_routes
app.include_router(options_routes.router)
app.include_router(opt_analysis_routes.router)
app.include_router(volatility_routes.router)
app.include_router(nse_routes.router, prefix="/api/v1/nse", tags=["nse"])
app.include_router(audit_routes.router, prefix="/api/audit", tags=["audit"])
app.include_router(macro_routes.router)
from backend.web.api import chat_widgets_routes
app.include_router(chat_widgets_routes.router)
app.include_router(ai_router)
app.include_router(mutual_fund_routes.router)


@app.on_event("startup")
async def startup_event():
    # Initialize DB
    # Base.metadata.create_all(bind=engine)


    print("Initializing Database...")
    try:
        from backend.ingest.nse_models import DividendDatabank
        DividendDatabank.__table__.create(bind=engine, checkfirst=True)
        print("DividendDatabank table initialized.")
    except Exception as e:
        print(f"Error creating DividendDatabank table: {e}")

    try:
        # Base.metadata.create_all(bind=engine)

        # Patch newly added columns for existing schema because Alembic is currently bypassed
        from sqlalchemy import text
        cols = [
            ("near_fut_close", "FLOAT"),
            ("next_fut_close", "FLOAT"),
            ("far_fut_close", "FLOAT"),
            ("delivery_pct_avg", "FLOAT"),
            ("highest_delivery_pct", "FLOAT"),
            ("eq_vol_avg", "FLOAT"),
            ("highest_eq_vol", "FLOAT"),
            ("z_score", "FLOAT"),
            ("eq_close_price", "FLOAT"),
            ("total_eq_volume", "FLOAT"),
            ("delivery_pct", "FLOAT"),
            ("atm_straddle_near_month", "FLOAT"),
            ("atm_straddle_weekly_nifty", "FLOAT"),
            ("highest_eq_vol_date", "DATE"), ("variance_252", "FLOAT"), ("covariance_252", "FLOAT")
        ]
        for col_name, col_type in cols:
            try:
                with engine.begin() as conn:
                    # Execute raw SQL directly for safety against Alembic divergence
                    conn.execute(text(f"ALTER TABLE daily_derivatives_analysis ADD COLUMN {col_name} {col_type};"))
                    print(f"Successfully added column {col_name} to daily_derivatives_analysis")
            except Exception:
                # Ignore DuplicateColumn errors
                pass
    except Exception as e:
        print(f"⚠️ Metadata Create Warning: {e}")

    try:
        TickVault().init_db()
        print("✅ TickVault initialized")
    except Exception as e:
        print(f"⚠️ TickVault Init Warning: {e}")

    # TimescaleDB setup requires ALTER TABLE queries which demand AccessExclusiveLocks.
    # Running this on every startup deadlocks the entire application (Celery inserts & UI reads)
    # if the tables are large. It should only be triggered manually via the UI config endpoint
    # (/api/v1/nse/setup-timescale) when absolutely necessary.
    print("⏩ Skipping automatic TimescaleDB policy setup to prevent table deadlocks. Trigger manually if needed.")

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

@app.get("/derivatives")
async def get_derivatives():
    return FileResponse("backend/ui/templates/derivatives.html")

@app.get("/strategy-composer")
async def get_strategy_composer():
    return FileResponse("backend/ui/templates/strategy_composer.html")
