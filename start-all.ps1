# GuardianAI - Start backend + frontend (run in one terminal with two jobs, or use two terminals)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Ensure Node is on PATH
$nodePath = "C:\Program Files\nodejs"
if (Test-Path $nodePath) { $env:Path = "$nodePath;" + $env:Path }

Write-Host "=== GuardianAI Setup Check ===" -ForegroundColor Cyan

# Backend .env
if (-not (Test-Path "$root\backend\.env")) {
    Copy-Item "$root\backend\.env.example" "$root\backend\.env"
}

# Frontend .env.local
if (-not (Test-Path "$root\frontend\.env.local")) {
    Copy-Item "$root\frontend\.env.local.example" "$root\frontend\.env.local"
}

Write-Host ""
Write-Host "Open TWO terminals and run:" -ForegroundColor Yellow
Write-Host "  Terminal 1:  .\start-backend.ps1" -ForegroundColor White
Write-Host "  Terminal 2:  .\start-frontend.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Then open:" -ForegroundColor Green
Write-Host "  Dashboard:  http://localhost:3000" -ForegroundColor White
Write-Host "  API docs:   http://127.0.0.1:8000/docs" -ForegroundColor White
