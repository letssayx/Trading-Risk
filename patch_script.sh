#!/bin/bash
# Apply fixes again if they somehow got lost or if there are other files like venv-wsl/bin/uvicorn running.
# Let's see if watchfiles is still erroring because of `--reload` trying to load everything instead of just `backend/`
sed -i 's/--reload/--reload --reload-dir backend/g' run.sh
sed -i 's/--reload --reload-dir backend --reload-dir backend/--reload --reload-dir backend/g' run.sh
