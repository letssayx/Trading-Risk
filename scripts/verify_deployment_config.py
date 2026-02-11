import os
import sys

def verify_deployment():
    print("Verifying Deployment Configuration...")

    files = [
        "docker-compose.yml",
        "setup.sh",
        "run_dev.sh",
        "requirements.txt",
        ".env.template",
        ".cursorrules",
        "backend/celery_worker.py"
    ]

    all_ok = True
    for f in files:
        exists = os.path.exists(f)
        print(f"[{'OK' if exists else 'FAIL'}] {f}")
        if not exists: all_ok = False

    if not all_ok:
        print("Missing critical deployment files.")
        sys.exit(1)

    # Check Content
    with open("docker-compose.yml") as f:
        content = f.read()
        if "timescaledb" not in content or "redis" not in content:
            print("[FAIL] docker-compose.yml missing services")
            sys.exit(1)

    print("\n[SUCCESS] Deployment Config Verified.")

if __name__ == "__main__":
    verify_deployment()
