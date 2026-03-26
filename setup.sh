#!/bin/bash

# Turtle Terminal - WSL2 Setup Script

echo ">>> Initializing Turtle Terminal Environment..."

# 1. Create Virtual Environment
if [ ! -d "venv" ]; then
    echo ">>> Creating Python Virtual Environment (venv)..."
    python3 -m venv venv
else
    echo ">>> venv already exists."
fi

# 2. Activate & Install
source venv/bin/activate
echo ">>> Upgrading pip..."
pip install --upgrade pip

echo ">>> Installing Dependencies from requirements.txt..."
pip install -r requirements.txt

# 3. Database Initialization (Assuming Docker is running)
echo ">>> Waiting for Docker services..."
# In a real script, we might check `docker ps`. Here we assume user runs run_dev.sh later.

# 4. Create .env from template if missing
if [ ! -f ".env" ]; then
    echo ">>> Creating .env from template..."
    cp .env.template .env
fi

echo ">>> Setup Complete. Run './run_dev.sh' to start the terminal."
