# Create Python virtual environment
Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor Cyan
python -m venv .venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .venv\Scripts\Activate.ps1


# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install PyTorch with CUDA 12.6 support (pinned stable version matching Python 3.10 and Windows CUDA capabilities)
Write-Host "Installing PyTorch with CUDA 12.6 support..." -ForegroundColor Cyan
pip install torch==2.8.0+cu126 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# Install requirements
Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Cyan
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu126

# Install WhisperX from GitHub
Write-Host "Installing WhisperX from GitHub..." -ForegroundColor Cyan
pip install git+https://github.com/m-bain/whisperX.git --extra-index-url https://download.pytorch.org/whl/cu126

# Verify PyTorch installation and CUDA availability
Write-Host "Verifying installation..." -ForegroundColor Cyan
python -c "
import torch
print('========================================')
print(f'PyTorch Version: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA Device Name: {torch.cuda.get_device_name(0)}')
    print(f'CUDA Device Count: {torch.cuda.device_count()}')
else:
    print('WARNING: CUDA is NOT available. Whisper models will run on CPU, which is very slow!')
print('========================================')
"

Write-Host "Installation completed!" -ForegroundColor Green
