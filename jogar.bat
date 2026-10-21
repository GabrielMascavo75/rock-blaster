@echo off
cd /d "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
    echo Instalando o uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
)
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

echo Iniciando o Rock Blaster (a primeira vez pode levar alguns minutos)...
uv run --python 3.12 --with-requirements requirements.txt rock_blaster.py
if errorlevel 1 (
    echo.
    echo Ocorreu um erro. Veja a secao "Solucao de problemas" no README.
)
pause
