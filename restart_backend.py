import subprocess
import time

# Kill existing uvicorn
subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
print("Killed uvicorn")

# Wait a second
time.sleep(1)

# Start uvicorn
import os
os.system("cd backend && uvicorn web.main:app --host 0.0.0.0 --port 8000 --reload &> uvicorn_output.log &")
print("Started uvicorn")
time.sleep(3)
