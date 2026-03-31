import os
import subprocess
import time

res = subprocess.run(["PYTHONPATH=$(pwd) python -c 'import backend.web.main'"], shell=True, capture_output=True, text=True)
print("Import check:")
print(res.stderr)
