@echo off
title Console de Transcricao ^& Diarizacao
chcp 65001 > nul

:: Verificacao do ambiente virtual
if not exist .venv (
    echo [!] ERRO: Ambiente virtual .venv nao encontrado!
    echo     Por favor, execute o script install_gpu.ps1 primeiro.
    pause
    exit /b
)

:: Caso o usuario arraste um arquivo diretamente para o arquivo .bat
if "%~1" NEQ "" (
    echo [*] Arquivo detectado via arrastar-e-soltar: %1
    echo [*] Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
    echo [*] Iniciando transcricao recomendada...
    python transcribe.py %1 --device cuda --model medium --compute_type int8 --batch_size 1 --language pt --vad-onset 0.1 --vad-offset 0.1
    echo.
    echo [*] Concluido!
    pause
    exit /b
)

:: Inicializacao normal (Console Interativo)
call .venv\Scripts\activate.bat
python transcribe.py --interactive
echo.
echo [*] Execucao encerrada.
pause
