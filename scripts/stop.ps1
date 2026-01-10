$ErrorActionPreference = 'Continue'

Write-Host "Stopping backend and frontend processes..."

# Stop Python/uvicorn processes on port 8000
$backendProcs = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }

if ($backendProcs) {
    $backendProcs | Stop-Process -Force
    Write-Host "Stopped backend processes"
} else {
    Write-Host "No backend process found on port 8000"
}

# Stop Node/Vite processes on port 5173
$frontendProcs = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }

if ($frontendProcs) {
    $frontendProcs | Stop-Process -Force
    Write-Host "Stopped frontend processes"
} else {
    Write-Host "No frontend process found on port 5173"
}

Write-Host "Done."
