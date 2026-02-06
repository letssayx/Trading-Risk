#!/bin/bash

echo "🐢 Setting up Turtle Terminal Environment..."

# 1. Create Virtual Env
if [ ! -d "venv" ]; then
    echo "Creating Python Virtual Environment..."
    python3 -m venv venv
fi

# 2. Activate
source venv/bin/activate

# 3. Install Dependencies
echo "Installing Dependencies..."
pip install -r requirements.txt

# 4. Environment Check
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.template..."
    cp .env.template .env
    echo "Please update .env with your real credentials."
fi

echo "✅ Setup Complete. Run './run_dev.sh' to start."
