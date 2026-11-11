@echo off
REM Abre Alfred en modo texto. Agrega --voz para hablarle: Alfred.bat --voz
chcp 65001 >nul
cd /d "%~dp0"
.venv\Scripts\python.exe -m alfred %*
pause
