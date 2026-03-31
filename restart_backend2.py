import os
import subprocess
import time

# Kill existing uvicorn
subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)

# Run standard dev script to properly set PYTHONPATH
os.system("PYTHONPATH=$PYTHONPATH:$(pwd) uvicorn backend.web.main:app --host 0.0.0.0 --port 8000 --reload &> uvicorn_output.log &")
print("Started uvicorn via module path")
time.sleep(3)
