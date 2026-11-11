#!/bin/bash
# Instalador de Alfred para Mac. Haz doble clic en este archivo
# (si macOS lo bloquea: clic derecho → Abrir).
cd "$(dirname "$0")" || exit 1
echo ""
echo "=== Instalando Alfred ==="

if ! command -v python3 >/dev/null 2>&1; then
  echo "No encontré Python 3. Instálalo desde https://www.python.org/downloads/ y vuelve a abrir este archivo."
  read -r -p "Presiona Enter para salir"; exit 1
fi

[ -d .venv ] || python3 -m venv .venv || exit 1
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt || { echo "Falló la instalación."; read -r -p "Enter para salir"; exit 1; }

echo ""
echo "Instalando la voz (opcional)..."
if command -v brew >/dev/null 2>&1; then
  brew install portaudio && .venv/bin/pip install SpeechRecognition pyttsx3 pyaudio \
    || echo "  La voz no se pudo instalar; Alfred funciona igual por texto."
else
  echo "  Para la voz instala Homebrew (https://brew.sh) y vuelve a abrir este archivo."
fi

if [ ! -f .env ]; then
  cp .env.ejemplo .env
  echo "Creé el archivo .env: ábrelo con TextEdit y pon tus claves (open -e .env)."
fi

echo ""
read -r -p "¿Quieres que Alfred arranque solo al encender el Mac (avisos, noticias, Telegram)? (s/n) " AUTO
if [ "$AUTO" = "s" ] || [ "$AUTO" = "S" ]; then
  PLIST="$HOME/Library/LaunchAgents/cl.alfred.servicio.plist"
  mkdir -p "$HOME/Library/LaunchAgents" datos_alfred
  cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>cl.alfred.servicio</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PWD/.venv/bin/python</string><string>-m</string><string>alfred</string><string>--servicio</string>
  </array>
  <key>WorkingDirectory</key><string>$PWD</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$PWD/datos_alfred/alfred.log</string>
  <key>StandardErrorPath</key><string>$PWD/datos_alfred/alfred.log</string>
</dict>
</plist>
PLIST
  launchctl unload "$PLIST" 2>/dev/null
  launchctl load "$PLIST" && echo "Listo: Alfred arrancará en segundo plano al iniciar sesión."
  echo "Si macOS pregunta si Python puede acceder a Descargas o Escritorio, acepta para organizar archivos."
fi

chmod +x Alfred.command
echo ""
echo "=== Instalación terminada ==="
echo "Para hablar con Alfred: doble clic en Alfred.command"
read -r -p "Presiona Enter para cerrar"
