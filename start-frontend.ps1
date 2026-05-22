# GuardianAI - Start Frontend
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\frontend"

# Prefer system Node.js; fall back to Cursor bundled node
$node = $null
if (Get-Command node -ErrorAction SilentlyContinue) { $node = "node" }
elseif (Test-Path "C:\Program Files\nodejs\node.exe") { $node = "C:\Program Files\nodejs\node.exe" }
elseif (Test-Path "$env:LOCALAPPDATA\Programs\node\node.exe") { $node = "$env:LOCALAPPDATA\Programs\node\node.exe" }

if (-not $node) {
    Write-Host "ERROR: Node.js is not installed."
    Write-Host "Install from https://nodejs.org/ (LTS), then restart terminal and run this script again."
    exit 1
}

if (-not (Test-Path ".env.local")) {
    Copy-Item .env.local.example .env.local
    Write-Host "Created .env.local"
}

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm packages (first run)..."
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        npm install
    } else {
        & $node "$(Split-Path $node)\npm.cmd" install 2>$null
        if ($LASTEXITCODE -ne 0) { npm install }
    }
}

Write-Host "Starting GuardianAI Dashboard at http://localhost:3000"
if (Get-Command npm -ErrorAction SilentlyContinue) {
    npm run dev
} else {
    & $node node_modules\next\dist\bin\next dev
}
