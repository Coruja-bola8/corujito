@echo off
:: ============================================================
:: SGAUM - Configurador do Pen Drive Portatil
:: Execute UMA VEZ em qualquer maquina com Python e internet
:: Os pacotes ficam no pen drive - funciona em qualquer letra
:: ============================================================

set RAIZ=%~dp0
if "%RAIZ:~-1%"=="\" set RAIZ=%RAIZ:~0,-1%

echo ============================================================
echo  SGAUM - Configuracao do Modo Portatil
echo  Pasta detectada: %RAIZ%
echo ============================================================
echo.

:: Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado.
    echo Instale em: https://www.python.org/downloads/
    echo Marque "Add Python to PATH"
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v encontrado.

:: Criar estrutura de pastas
echo.
echo [1/3] Criando estrutura de pastas...
if not exist "%RAIZ%\pacotes"           mkdir "%RAIZ%\pacotes"
if not exist "%RAIZ%\sistema\instance"  mkdir "%RAIZ%\sistema\instance"
if not exist "%RAIZ%\backups"           mkdir "%RAIZ%\backups"
echo [OK] Pastas criadas.

:: Instalar pacotes direto na pasta 'pacotes' do pen drive
echo.
echo [2/3] Instalando pacotes no pen drive (requer internet)...
echo Isso pode levar 2-3 minutos...
python -m pip install --target="%RAIZ%\pacotes" --upgrade ^
    flask flask-sqlalchemy flask-login flask-migrate werkzeug -q
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar. Verifique sua conexao com a internet.
    pause
    exit /b 1
)
echo [OK] Pacotes instalados em: %RAIZ%\pacotes\

:: Testar se o Flask foi instalado corretamente
echo.
echo [3/3] Testando instalacao...
set PYTHONPATH=%RAIZ%\pacotes
python -c "import flask; print('[OK] Flask', flask.__version__, 'funcionando.')"
if %errorlevel% neq 0 (
    echo [ERRO] Teste falhou. Tente executar este script novamente.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Configuracao concluida com sucesso!
echo.
echo  COMO USAR EM QUALQUER MAQUINA:
echo  1. Conecte o pen drive
echo  2. Clique duas vezes em: iniciar_portatil.bat
echo  3. Acesse: http://localhost:5000
echo.
echo  Requisito: Python instalado na maquina (gratuito)
echo  Download:  https://www.python.org/downloads/
echo ============================================================
echo.
pause
