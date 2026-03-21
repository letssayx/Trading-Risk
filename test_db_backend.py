import subprocess
import time

def start_backend():
    print("Starting Uvicorn backend...")
    proc = subprocess.Popen(
        ["uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    time.sleep(3)  # Give it a moment to start
    return proc

if __name__ == "__main__":
    proc = start_backend()
