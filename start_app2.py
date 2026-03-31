import os
import subprocess
import time

subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)

# Run standard dev script to properly set PYTHONPATH
os.system("PYTHONPATH=$(pwd) uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > uvicorn_output.log 2>&1 &")
print("Started uvicorn via backend.main:app")
time.sleep(3)
