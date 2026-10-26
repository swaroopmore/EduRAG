<#
  Starts EduRAG on this PC and publishes it through your free ngrok domain.

  Usage (PowerShell, from anywhere):
    powershell -ExecutionPolicy Bypass -File .\start-edurag.ps1 -Domain jumpy-red-mollusk.ngrok-free.app

  It opens two windows: the API (only reachable from this PC) and the ngrok tunnel.
  Close both windows to take the site offline.
#>
param(
  [Parameter(Mandatory = $true)][string]$Domain   # your free ngrok dev domain, with or without https://
)
$ErrorActionPreference = "Stop"

$backend = (Resolve-Path (Join-Path $PSScriptRoot "..\..\backend")).Path
$python  = Join-Path $backend ".venv\Scripts\python.exe"
$Domain  = ($Domain -replace '^https?://', '') -replace '/.*$', ''

if (-not (Test-Path $python)) { throw "Could not find $python. Create the virtual environment first (see LAPTOP_DEPLOY.md, step 1)." }
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) { throw "ngrok is not installed or not on PATH (see LAPTOP_DEPLOY.md, step 2)." }

# 1) API - bound to 127.0.0.1 so only the tunnel on this PC can reach it.
$apiCmd = "Set-Location '$backend'; & '$python' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips='*'"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCmd

Write-Host "Waiting for the API to start (the first start can take a minute while the AI models load)..."
$ok = $false
for ($i = 0; $i -lt 60; $i++) {
  try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 3
    if ($r.StatusCode -eq 200) { $ok = $true; break }
  } catch { Start-Sleep -Seconds 3 }
}
if (-not $ok) { throw "The API did not become healthy. Look at the API window for the error (often: Postgres is not running or .env is missing)." }
Write-Host "API is healthy."

# 2) Tunnel
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 8000 --url $Domain"

Write-Host ""
Write-Host "Public API address:  https://$Domain"
Write-Host "Check it:            https://$Domain/health"
