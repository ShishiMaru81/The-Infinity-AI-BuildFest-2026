# GuardianAI - Start Backend
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\backend"

if (-not (Test-Path "venv\Scripts\uvicorn.exe")) {
    Write-Host "Creating venv and installing dependencies (first run only)..."
    python -m venv venv
    .\venv\Scripts\pip install -r requirements.txt
}

if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example"
}

Write-Host "Starting GuardianAI API at http://127.0.0.1:8000"
Write-Host "API docs: http://127.0.0.1:8000/docs"
.\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
