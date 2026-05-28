# Launch Speech Studio App
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "         A iniciar o Speech Studio...            " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

if (-not (Test-Path ".venv")) {
    Write-Host "[!] Ambiente virtual .venv nao encontrado. Rode install_gpu.ps1 primeiro!" -ForegroundColor Red
    Exit 1
}

# Activate virtual environment
& .venv\Scripts\Activate.ps1

# Run the app launcher
python app.py --port 7860 --server-name 127.0.0.1
