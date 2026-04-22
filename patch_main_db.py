with open("backend/main.py", "r") as f:
    text = f.read()

# Make sure tables are created on startup
startup_code = """
@app.on_event("startup")
async def startup_event():
    # Initialize DB
    import backend.ingest.nse_models
    from backend.infrastructure.db import engine, Base
    Base.metadata.create_all(bind=engine)
"""

text = text.replace("@app.on_event(\"startup\")\nasync def startup_event():\n    # Initialize DB", startup_code)

with open("backend/main.py", "w") as f:
    f.write(text)
