# Windows PowerShell Setup Script
Write-Host "Setting up Autonomous AI QA Engineer environment..." -ForegroundColor Green

# 1. Python virtual environment
if (-not (Test-Path "backend\venv")) {
    Write-Host "Creating Python virtual environment in backend\venv..."
    python -m venv backend\venv
}

# 2. Install Python packages
Write-Host "Installing Python backend packages..."
.\backend\venv\Scripts\pip install -r backend\requirements.txt

# 3. Install Playwright browser
Write-Host "Installing Playwright chromium browser binaries..."
.\backend\venv\Scripts\playwright.exe install chromium

# 4. Install Frontend dependencies
Write-Host "Installing frontend node packages..."
cd frontend
npm install
npm run build
cd ..

Write-Host "Setup completed successfully! Run .\backend\venv\Scripts\python.exe scripts\run_demo.py to start." -ForegroundColor Green
