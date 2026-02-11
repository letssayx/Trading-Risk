from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

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

@app.get("/")
def read_root():
    return {"status": "Turtle Terminal Active"}


@app.get("/dashboard", response_class=HTMLResponse)
def read_dashboard():
    """
    Serves the Turtle Workbench UI from the HTML template.
    """
    template_path = (
        Path(__file__).resolve().parent / "ui" / "templates" / "workbench.html"
    )
    return template_path.read_text(encoding="utf-8")
