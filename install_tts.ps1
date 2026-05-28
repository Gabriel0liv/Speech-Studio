# Speech Studio TTS Installer
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Instalador de Dependencias de TTS e App UI     " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Activate virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "[!] Ambiente virtual .venv nao encontrado. Rode install_gpu.ps1 ou install_cpu.ps1 primeiro!" -ForegroundColor Red
    Exit 1
}

Write-Host "[*] A ativar o ambiente virtual (.venv)..." -ForegroundColor Cyan
& .venv\Scripts\Activate.ps1

Write-Host "[*] A instalar pacotes de requirements-tts.txt..." -ForegroundColor Cyan
pip install -r requirements-tts.txt

# Verify installation of Kokoro and Piper in Python
Write-Host "[*] A verificar importacoes..." -ForegroundColor Cyan
python -c "
try:
    import gradio as gr
    print('Gradio importado com sucesso!')
except ImportError:
    print('AVISO: Gradio nao pode ser importado.')
try:
    import kokoro
    print('Kokoro importado com sucesso!')
except ImportError:
    print('AVISO: Kokoro nao pode ser importado.')
try:
    import piper
    print('Piper importado com sucesso!')
except ImportError:
    print('AVISO: Piper nao pode ser importado.')
"

# Check for espeak-ng installation
Write-Host "[*] A verificar dependencia do eSpeak NG..." -ForegroundColor Cyan
$espeakInstalled = python -c "
import sys, os
sys.path.append(os.path.dirname(os.path.abspath('.')))
from src.tts.kokoro_engine import setup_espeak
print(setup_espeak())
"

if ($espeakInstalled -eq "True") {
    Write-Host "[+] eSpeak NG foi detectado no sistema! O Speech Studio esta pronto para rodar." -ForegroundColor Green
} else {
    Write-Host "--------------------------------------------------" -ForegroundColor Yellow
    Write-Host "[!] IMPORTANTE: O eSpeak NG NAO foi detectado no seu sistema!" -ForegroundColor Yellow
    Write-Host "O Kokoro e o Piper exigem o eSpeak NG para funcionar no Windows." -ForegroundColor Yellow
    Write-Host "Para instalar:" -ForegroundColor Yellow
    Write-Host "  1. Baixe o instalador (.msi) do site:" -ForegroundColor White
    Write-Host "     https://github.com/espeak-ng/espeak-ng/releases" -ForegroundColor Cyan
    Write-Host "  2. Procure pela versao mais recente (ex: espeak-ng-X.XX-x64.msi) e instale." -ForegroundColor White
    Write-Host "  3. O instalador deve adicionar o eSpeak NG ao seu PATH automaticamente." -ForegroundColor White
    Write-Host "  4. Se persistirem problemas, reinicie o computador para aplicar as mudancas de PATH." -ForegroundColor White
    Write-Host "--------------------------------------------------" -ForegroundColor Yellow
}

Write-Host "[+] Instalacao concluida!" -ForegroundColor Green
