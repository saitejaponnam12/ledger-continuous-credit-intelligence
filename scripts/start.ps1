# LEDGER — One-Click Setup & Run Script (PowerShell)
# Run: .\scripts\start.ps1
# Requires: Python 3.11+, Node.js 18+, PostgreSQL 15

param(
    [switch]$SetupOnly,
    [switch]$SkipInstall,
    [switch]$DemoMode
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  LEDGER — Continuous Credit Intelligence" -ForegroundColor White
Write-Host "  One-Click Setup" -ForegroundColor Gray
Write-Host "============================================================`n" -ForegroundColor Cyan

# ── Check prerequisites ─────────────────────────────────────
function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }

if (!(Test-Command python)) { Write-Error "Python not found. Install Python 3.11+ first." }
if (!(Test-Command node)) { Write-Error "Node.js not found. Install Node.js 18+ first." }
if (!(Test-Command psql)) { Write-Warning "psql not found. Database setup will need to be done manually." }

Write-Host "[1/7] Checking Python version..." -ForegroundColor Yellow
$pyVersion = python --version 2>&1
Write-Host "  $pyVersion" -ForegroundColor Gray

# ── Python virtual environment ──────────────────────────────
if (!$SkipInstall) {
    Write-Host "[2/7] Setting up Python virtual environment..." -ForegroundColor Yellow
    $venvPath = "$Root\backend\.venv"
    if (!(Test-Path $venvPath)) {
        python -m venv $venvPath
        Write-Host "  Created .venv at $venvPath" -ForegroundColor Gray
    }

    Write-Host "[3/7] Installing Python dependencies..." -ForegroundColor Yellow
    & "$venvPath\Scripts\pip.exe" install -r "$Root\backend\requirements.txt" --quiet
    Write-Host "  Dependencies installed." -ForegroundColor Green

    # Install structlog if not in requirements
    & "$venvPath\Scripts\pip.exe" install structlog --quiet
} else {
    Write-Host "[2-3/7] Skipping install (--SkipInstall)" -ForegroundColor Gray
    $venvPath = "$Root\backend\.venv"
}

$pythonExe = "$venvPath\Scripts\python.exe"

# ── Database setup ──────────────────────────────────────────
Write-Host "[4/7] Setting up database..." -ForegroundColor Yellow
$pgCheck = psql -U postgres -c "SELECT 1" 2>&1
if ($LASTEXITCODE -eq 0) {
    # Create DB and user
    psql -U postgres -c "CREATE USER ledger_user WITH PASSWORD 'ledger_pass';" 2>&1 | Out-Null
    psql -U postgres -c "CREATE DATABASE ledger_db OWNER ledger_user;" 2>&1 | Out-Null
    psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ledger_db TO ledger_user;" 2>&1 | Out-Null
    
    # Enable pgvector
    psql -U postgres -d ledger_db -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>&1 | Out-Null
    Write-Host "  Database and pgvector ready." -ForegroundColor Green
} else {
    Write-Host "  PostgreSQL not reachable. Ensure it is running." -ForegroundColor Yellow
    Write-Host "  Expected: postgresql+asyncpg://ledger_user:ledger_pass@localhost:5432/ledger_db" -ForegroundColor Gray
}

# ── Python setup ──────────────────────────────────────────────
Write-Host "[5/7] Initializing database schema and seed data..." -ForegroundColor Yellow
Push-Location "$Root\backend"
try {
    & $pythonExe -c "import sys; sys.path.insert(0, '.'); from app.core.config import settings; print('Config OK')"
    & $pythonExe "$Root\scripts\setup_db.py"
    Write-Host "  Schema created, users seeded." -ForegroundColor Green
} catch {
    Write-Host "  DB setup skipped: $_" -ForegroundColor Yellow
}
Pop-Location

# ── Generate synthetic data + train model ──────────────────
Write-Host "[6/7] Training ML model..." -ForegroundColor Yellow
Push-Location "$Root"
try {
    & $pythonExe -c "
import sys
sys.path.insert(0, 'backend')
from backend.seed.synthetic_generator import generate_synthetic_dataset, save_demo_personas
generate_synthetic_dataset()
save_demo_personas()
"
    & $pythonExe "ml\train.py"
    Write-Host "  XGBoost model trained and calibrated." -ForegroundColor Green
} catch {
    Write-Host "  ML training skipped: $_" -ForegroundColor Yellow
}
Pop-Location

# ── Ingest policies ────────────────────────────────────────
Push-Location "$Root"
try {
    & $pythonExe "scripts\ingest_policies.py"
    Write-Host "  Policy documents embedded in pgvector." -ForegroundColor Green
} catch {
    Write-Host "  Policy ingestion skipped: $_" -ForegroundColor Yellow
}
Pop-Location

# ── Frontend ──────────────────────────────────────────────
if (!$SkipInstall) {
    Write-Host "  Installing frontend dependencies..." -ForegroundColor Gray
    Push-Location "$Root\frontend"
    npm install --silent
    Pop-Location
}

Write-Host "`n[7/7] Setup complete!`n" -ForegroundColor Green

if ($SetupOnly) {
    Write-Host "Setup only mode. Exiting." -ForegroundColor Gray
    exit 0
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Starting LEDGER..." -ForegroundColor White
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:5173" -ForegroundColor Cyan
Write-Host "  API Docs:  http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host "  Login:     sarah.chen@ledger.demo / LedgerDemo2026!`n" -ForegroundColor Yellow

# Start backend in background
$backendJob = Start-Job -ScriptBlock {
    param($root, $venv)
    Push-Location "$root\backend"
    & "$venv\Scripts\uvicorn.exe" app.main:app --reload --host 0.0.0.0 --port 8000
    Pop-Location
} -ArgumentList $Root, $venvPath

# Start frontend in background
$frontendJob = Start-Job -ScriptBlock {
    param($root)
    Push-Location "$root\frontend"
    npm run dev
    Pop-Location
} -ArgumentList $Root

Write-Host "Both services starting..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop.`n" -ForegroundColor Gray

# Wait and stream output
try {
    while ($true) {
        Receive-Job $backendJob | ForEach-Object { Write-Host "[backend] $_" -ForegroundColor DarkGray }
        Receive-Job $frontendJob | ForEach-Object { Write-Host "[frontend] $_" -ForegroundColor DarkGray }
        Start-Sleep 1
    }
} finally {
    Stop-Job $backendJob, $frontendJob
    Remove-Job $backendJob, $frontendJob
}
