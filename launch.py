import os
import sys
import subprocess
import time
import webbrowser
import platform
import socket

def is_port_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def start_server():
    print("🐢 Starting Turtle Terminal Server...")
    # Determine command based on OS/Environment
    cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"]

    # In dev mode, we might want reload, but launcher implies "Production/App Mode" usage usually.
    # We'll default to standard run.
    if os.getenv("ENV") == "dev":
        cmd.append("--reload")

    # Start process
    if platform.system() == "Windows":
        process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        process = subprocess.Popen(cmd)

    return process

def open_browser_app_mode(url):
    print(f"🚀 Launching App Mode: {url}")
    system = platform.system()

    try:
        if system == "Windows":
            # Try Chrome then Edge
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(chrome_path):
                subprocess.Popen([chrome_path, f"--app={url}"])
                return
            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            if os.path.exists(edge_path):
                subprocess.Popen([edge_path, f"--app={url}"])
                return

        elif system == "Darwin": # macOS
            # Chrome on Mac
            subprocess.Popen(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", f"--app={url}"])
            return

        elif system == "Linux":
            # Chromium or Chrome
            subprocess.Popen(["google-chrome", f"--app={url}"])
            return

    except Exception as e:
        print(f"⚠️ Could not launch app mode: {e}")
        print("Falling back to default browser...")
        webbrowser.open(url)

def main():
    server_process = None
    try:
        # 1. Start Server
        if not is_port_open("127.0.0.1", 8000):
            server_process = start_server()

            # Wait for server to be ready
            print("Waiting for server to initialize...")
            retries = 30
            while not is_port_open("127.0.0.1", 8000) and retries > 0:
                time.sleep(1)
                retries -= 1

            if retries == 0:
                print("❌ Server failed to start.")
                return
        else:
            print("ℹ️ Server already running.")

        # 2. Launch Client
        open_browser_app_mode("http://127.0.0.1:8000/workbench")

        print("\n✅ Turtle Terminal Active.")
        print("Press Ctrl+C to exit.")

        # Keep script running if we started the server
        if server_process:
            server_process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        if server_process:
            server_process.terminate()

if __name__ == "__main__":
    main()
