@echo off
set RAIZ=%~dp0
if "%RAIZ:~-1%"=="\" set RAIZ=%RAIZ:~0,-1%

set DT=%date:~6,4%%date:~3,2%%date:~0,2%
set HR=%time:~0,2%%time:~3,2%
set HR=%HR: =0%

if not exist "%RAIZ%\backups" mkdir "%RAIZ%\backups"

if exist "%RAIZ%\sistema\instance\dados.db" (
    copy "%RAIZ%\sistema\instance\dados.db" "%RAIZ%\backups\dados_%DT%_%HR%.db" >nul
    echo [OK] Backup salvo: %RAIZ%\backups\dados_%DT%_%HR%.db
) else (
    echo [AVISO] Banco nao encontrado em: %RAIZ%\sistema\instance\dados.db
)
pause
