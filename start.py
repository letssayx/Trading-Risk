import subprocess
import time
import requests

proc = subprocess.Popen(["python3", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"])
time.sleep(10)
try:
    requests.get("http://localhost:8000/workbench")
    print("Server is up!")
except Exception as e:
    print("Server failed to start:", e)
