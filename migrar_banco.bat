@echo off
set RAIZ=%~dp0
if "%RAIZ:~-1%"=="\" set RAIZ=%RAIZ:~0,-1%

echo ============================================================
echo  SGAUM - Migracao do banco de dados
echo  Atualiza o banco existente sem perder dados
echo ============================================================
echo  Drive detectado: %RAIZ%
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado.
    pause
    exit /b 1
)

if not exist "%RAIZ%\sistema\instance\dados.db" (
    echo [AVISO] Banco nao encontrado. O sistema criara um novo banco ao iniciar.
    pause
    exit /b 0
)

set PYTHONPATH=%RAIZ%\pacotes
cd /d "%RAIZ%\sistema"
python migrar_banco.py
