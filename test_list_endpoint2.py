import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from backend.infrastructure.db import SessionLocal
from backend.web.api.data.view_routes import list_data
import os

async def main():
    db = SessionLocal()
    try:
        res = await list_data(type='dividend', limit=5, db=db)
        print("Success! Got", len(res), "rows")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(main())
