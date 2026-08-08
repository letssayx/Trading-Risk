import sys
sys.path.append('.')
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import DividendDatabank
from backend.ingest.tasks import build_dividend_databank_task

db = SessionLocal()

print("--- BEFORE FORCE REBUILD ---")
dlf = db.query(DividendDatabank).filter(DividendDatabank.symbol == 'DLF').all()
print(f"DLF rows: {len(dlf)}")
for d in dlf:
    print(f"DLF: id={d.id}, type={d.dividend_type}, amount={d.amount}, ex={d.ex_date}, bc={d.broadcast_date}")

coal = db.query(DividendDatabank).filter(DividendDatabank.symbol == 'COALINDIA', DividendDatabank.amount == 5.25).all()
for c in coal:
    print(f"COAL: id={c.id}, type={c.dividend_type}, amount={c.amount}, ex={c.ex_date}, bc={c.broadcast_date}, awaited={c.is_awaited}")

print("\nRunning build_dividend_databank_task(force=True)...")
try:
    # Creating a dummy self object since it's a celery bound task
    class DummyTask:
        pass
    build_dividend_databank_task(DummyTask(), force=True)
    print("Rebuild completed.")
except Exception as e:
    print(f"Rebuild failed: {e}")

print("\n--- AFTER FORCE REBUILD ---")
dlf = db.query(DividendDatabank).filter(DividendDatabank.symbol == 'DLF').all()
print(f"DLF rows: {len(dlf)}")
for d in dlf:
    print(f"DLF: id={d.id}, type={d.dividend_type}, amount={d.amount}, ex={d.ex_date}, bc={d.broadcast_date}")

coal = db.query(DividendDatabank).filter(DividendDatabank.symbol == 'COALINDIA', DividendDatabank.amount == 5.25).all()
for c in coal:
    print(f"COAL: id={c.id}, type={c.dividend_type}, amount={c.amount}, ex={c.ex_date}, bc={c.broadcast_date}, awaited={c.is_awaited}")

db.close()
