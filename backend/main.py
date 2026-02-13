from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.web import routes
from backend.web.portfolio import routes as portfolio_routes
from backend.web.live import logs
from backend.web.widgets import routes as widget_routes

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

app.include_router(routes.router)
app.include_router(portfolio_routes.router)
app.include_router(logs.router)
app.include_router(widget_routes.router)

@app.on_event("startup")
async def startup_event():
    import asyncio
    asyncio.create_task(logs.log_generator())

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
