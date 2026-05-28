$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    throw "Virtual environment not found at .\.venv"
}

. .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-api.txt
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
