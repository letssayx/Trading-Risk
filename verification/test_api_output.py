from backend.web.api.data.view_routes import list_data
from backend.infrastructure.db import SessionLocal
import asyncio
from datetime import date

async def test_api_response():
    db = SessionLocal()
    try:
        # Simulate request for fo_volatility
        print("Testing fo_volatility...")
        data = await list_data(type='fo_volatility', limit=1, db=db)
        print(f"Data type: {type(data)}")
        if data:
            print(f"First row keys: {data[0].keys()}")
            print(f"First row values: {data[0]}")
        else:
            print("No data returned.")

        # Simulate request for bhavcopy_fo
        print("\nTesting bhavcopy_fo...")
        data = await list_data(type='bhavcopy_fo', limit=1, db=db)
        if data:
            print(f"First row keys: {data[0].keys()}")
            # Check for serialization issues
            import json
            try:
                json_str = json.dumps(data[0])
                print("Serialization Successful")
            except Exception as e:
                print(f"Serialization Failed: {e}")
                for k, v in data[0].items():
                    print(f"{k}: {type(v)} = {v}")
        else:
            print("No data returned.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_api_response())
