import subprocess
print("Starting postgres")
subprocess.run(["docker-compose", "up", "-d", "db"])
