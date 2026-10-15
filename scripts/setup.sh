#!/bin/bash
set -e

echo "Setting up Autonomous AI QA Engineer environment..."

# 1. Python venv
if [ ! -d "backend/venv" ]; then
    python3 -m venv backend/venv
fi

# 2. Python requirements
./backend/venv/bin/pip install -r backend/requirements.txt

# 3. Playwright browser
./backend/venv/bin/playwright install chromium

# 4. Frontend dependencies
cd frontend
npm install
npm run build
cd ..

echo "Setup completed successfully! Run ./backend/venv/bin/python scripts/run_demo.py to start."
