$ErrorActionPreference = "Stop"

$root = (Get-Location).Path
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; .\run_api.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; .\run_frontend.ps1"
