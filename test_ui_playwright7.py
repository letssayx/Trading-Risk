import subprocess
import time

def verify_ui():
    print("Checking running processes...")
    subprocess.run(["lsof", "-i", ":8000"])

if __name__ == "__main__":
    verify_ui()
