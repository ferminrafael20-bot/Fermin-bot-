@echo off
REM Instalador de Alfred para Windows. Haz doble clic en este archivo.
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo === Instalando Alfred ===
echo.

set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
  where python >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if not defined PY (
  echo No encontre Python. Instalalo desde https://www.python.org/downloads/
  echo y marca la casilla "Add python.exe to PATH". Luego vuelve a ejecutar este archivo.
  pause
  exit /b 1
)

if not exist .venv (
  %PY% -m venv .venv || goto :error
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt || goto :error
echo.
echo Instalando la voz (opcional)...
pip install SpeechRecognition pyttsx3 pyaudio || echo   La voz no se pudo instalar; Alfred funciona igual por texto.

if not exist .env (
  copy .env.ejemplo .env >nul
  echo Cree el archivo .env: abrelo con el Bloc de notas y pon tus claves.
)

echo.
set /p AUTO=Quieres que Alfred arranque solo al encender el PC (avisos, noticias, Telegram)? (s/n):
if /i "%AUTO%"=="s" (
  set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
  call :crear_inicio
  echo Listo: Alfred arrancara en segundo plano al iniciar sesion.
)

echo.
echo === Instalacion terminada ===
echo Para hablar con Alfred: doble clic en Alfred.bat
echo Para editar tus claves: abre el archivo .env con el Bloc de notas
pause
exit /b 0

:crear_inicio
> "%STARTUP%\Alfred.vbs" (
  echo Set sh = CreateObject^("WScript.Shell"^)
  echo sh.CurrentDirectory = "%CD%"
  echo sh.Run """%CD%\.venv\Scripts\pythonw.exe"" -m alfred --servicio", 0, False
)
start "" wscript "%STARTUP%\Alfred.vbs"
exit /b 0

:error
echo.
echo Algo fallo durante la instalacion. Revisa el mensaje de arriba.
pause
exit /b 1
