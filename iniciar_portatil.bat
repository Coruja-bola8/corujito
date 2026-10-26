@echo off
:: ============================================================
:: SGAUM - Modo Portatil
:: Usa o Python instalado na maquina + pacotes no pen drive
:: Funciona em qualquer letra de drive
:: ============================================================

set RAIZ=%~dp0
if "%RAIZ:~-1%"=="\" set RAIZ=%RAIZ:~0,-1%

echo ============================================================
echo  SGAUM - Sistema de Gestao Administrativa
echo  Modo Portatil - Pen Drive
echo ============================================================
echo  Drive detectado: %RAIZ%
echo ============================================================
echo.

:: Verificar Python na maquina
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado nesta maquina.
    echo.
    echo Instale o Python em: https://www.python.org/downloads/
    echo Marque "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)
echo [OK] Python encontrado.

:: Verificar se os pacotes estao no pen drive
if not exist "%RAIZ%\pacotes\flask" (
    echo [AVISO] Pacotes nao encontrados no pen drive.
    echo Execute: configurar_portatil.bat
    pause
    exit /b 1
)
echo [OK] Pacotes no pen drive encontrados.

:: Garantir pasta instance
if not exist "%RAIZ%\sistema\instance" mkdir "%RAIZ%\sistema\instance"

:: Definir PYTHONPATH para usar os pacotes do pen drive
:: Isso faz o Python da maquina usar os pacotes instalados no pen drive
set PYTHONPATH=%RAIZ%\pacotes

echo [OK] Iniciando servidor...
echo.
echo Acesse no navegador: http://localhost:5000
echo Para encerrar: feche esta janela ou pressione Ctrl+C
echo.

set SECRET_KEY=sgaum-portatil-2026
set FLASK_APP=app.py

cd /d "%RAIZ%\sistema"
python app.py
pause
