PYTHONPATH=. pyenv exec python3 -m uvicorn backend.main:app --port 8000 > backend_output.log 2>&1 &
