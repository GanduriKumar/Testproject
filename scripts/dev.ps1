$ErrorActionPreference = 'Stop'

# Determine repo root (this script is under scripts/)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path $scriptDir

Write-Host "Repo root: $repoRoot"

# Ensure PYTHONPATH so 'backend' package resolves
$env:PYTHONPATH = $repoRoot

# Start backend (no reload on Windows)
Write-Host "Starting backend on http://localhost:8000 ..."
$null = Start-Job -Name 'backend' -ScriptBlock {
  param($root)
  Set-Location $root
  python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
} -ArgumentList $repoRoot

# Start frontend Vite dev server
Write-Host "Starting frontend on http://localhost:5173 ..."
$null = Start-Job -Name 'frontend' -ScriptBlock {
  param($root)
  Set-Location (Join-Path $root 'frontend')
  npm run dev
} -ArgumentList $repoRoot

Write-Host "Jobs started. Use 'Receive-Job -Name backend' and 'Receive-Job -Name frontend' to view logs."
Write-Host "Stop with: Stop-Job -Name backend; Stop-Job -Name frontend"
