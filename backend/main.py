from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from backend.web import routes
from backend.web.portfolio import routes as portfolio_routes
from backend.web.live import logs
from backend.web.live import routes as live_routes
from backend.web.widgets import routes as widget_routes
from backend.web.jules import routes as jules_routes
from backend.web.edge import routes as edge_routes
from backend.web.strategies import adapters_routes
from backend.web.data import routes as data_routes # New Data API
from backend.audit.logger import AuditMiddleware

app = FastAPI(title="Turtle Terminal - Institutional Shell")

app.add_middleware(AuditMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/ui/static"), name="static")

app.include_router(routes.router)
app.include_router(portfolio_routes.router)
app.include_router(logs.router)
app.include_router(live_routes.router)
app.include_router(widget_routes.router)
app.include_router(jules_routes.router)
app.include_router(edge_routes.router)
app.include_router(adapters_routes.router)
app.include_router(data_routes.router)

@app.on_event("startup")
async def startup_event():
    import asyncio
    from backend.monitoring.health import monitor
    from backend.web.live.routes import start_broadcast

    # Start Background Tasks
    asyncio.create_task(logs.log_generator())
    asyncio.create_task(start_broadcast())

    # Start Self-Healing Monitor (Threaded)
    monitor.start()

@app.get("/")
async def root():
    return RedirectResponse(url="/workbench")

@app.get("/workbench")
async def get_workbench():
    return FileResponse("backend/ui/templates/workbench.html")
