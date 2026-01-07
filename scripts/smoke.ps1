$ErrorActionPreference = 'Stop'

param(
  [string]$BackendUrl = 'http://localhost:8000'
)

Write-Host "Checking $BackendUrl/health ..."
$h = Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing
if ($h.StatusCode -ne 200) { throw "Health check failed: $($h.StatusCode)" }
Write-Host "Health OK"

Write-Host "Listing datasets ..."
$d = Invoke-WebRequest -Uri "$BackendUrl/datasets" -UseBasicParsing
if ($d.StatusCode -ne 200) { throw "Datasets failed: $($d.StatusCode)" }
Write-Host "Datasets OK"

Write-Host "Done."
