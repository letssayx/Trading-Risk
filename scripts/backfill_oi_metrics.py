import sys
import os
import requests

# Add the root directory to PYTHONPATH if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We will use requests to hit the local fastapi server.
# Alternatively, we can just call the function directly if we set up the DB session.
# Calling the endpoint is safer if the app is already running.

print("Starting OI Analysis Backfill...")

try:
    response = requests.post("http://localhost:8000/api/data/analysis/oi/compute?days=500")
    if response.status_code == 200:
        print("Success:", response.json())
    else:
        print(f"Error {response.status_code}:", response.text)
except requests.exceptions.ConnectionError:
    print("Could not connect to the server. Make sure it is running on http://localhost:8000")
