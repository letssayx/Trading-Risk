from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.web import routes
from backend.web.portfolio import routes as portfolio_routes

app = FastAPI(title="Turtle Terminal - Institutional Shell")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
app.include_router(portfolio_routes.router)

from backend.web.live import logs
from backend.web.widgets import routes as widget_routes

app.include_router(logs.router)
app.include_router(widget_routes.router)

@app.on_event("startup")
async def startup_event():
    import asyncio
    asyncio.create_task(logs.log_generator())

@app.get("/")
def read_root():
    return {"status": "Turtle Terminal Active"}
