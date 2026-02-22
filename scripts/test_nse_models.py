from backend.infrastructure.db import Base
from backend.ingest import nse_models
import sys

try:
    print("Testing NSE Models Registration...")
    # List all tables registered in Base.metadata
    tables = Base.metadata.tables.keys()
    print("Registered Tables:")
    for t in tables:
        print(f" - {t}")

    expected_tables = [
        "bhavcopy_eq", "bhavcopy_fo", "fao_participant_oi",
        "fo_volatility", "block_deals", "bulk_deals",
        "fii_derivatives_stats", "mto_delivery",
        "mwpl_client_position", "security_master",
        "pe_ratio", "import_logs"
    ]

    missing = [t for t in expected_tables if t not in tables]

    if missing:
        print(f"❌ Missing tables: {missing}")
        sys.exit(1)
    else:
        print("✅ All NSE tables registered successfully.")

except Exception as e:
    print(f"❌ NSE Models Error: {e}")
    sys.exit(1)
