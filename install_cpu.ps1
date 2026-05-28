# Create Python virtual environment
Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor Cyan
python -m venv .venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install PyTorch CPU version
Write-Host "Installing PyTorch CPU version..." -ForegroundColor Cyan
pip install torch torchvision torchaudio

# Install requirements
Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Cyan
pip install -r requirements.txt

# Install WhisperX from GitHub
Write-Host "Installing WhisperX from GitHub..." -ForegroundColor Cyan
pip install git+https://github.com/m-bain/whisperX.git

# Verify PyTorch installation and CUDA availability
Write-Host "Verifying installation..." -ForegroundColor Cyan
python -c "
import torch
print('========================================')
print(f'PyTorch Version: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
print('System running on CPU.')
print('========================================')
"

Write-Host "CPU-only Installation completed!" -ForegroundColor Green
