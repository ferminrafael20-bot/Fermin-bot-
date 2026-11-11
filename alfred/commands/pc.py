"""Control del PC: abrir páginas y programas (también desde Telegram).

Ejemplos: "abre youtube", "abre shopify", "abre easycancha", "abre spotify",
"reserva una cancha".
Agrega tus sitios favoritos al diccionario SITIOS.
"""

import platform
import shutil
import subprocess
import webbrowser

from alfred.core import command, tool

SITIOS = {
    "youtube": "https://www.youtube.com", "youtube studio": "https://studio.youtube.com",
    "gmail": "https://mail.google.com", "correo": "https://mail.google.com",
    "calendario": "https://calendar.google.com", "drive": "https://drive.google.com",
    "shopify": "https://admin.shopify.com", "mi tienda": "https://admin.shopify.com",
    "easycancha": "https://www.easycancha.com", "easy cancha": "https://www.easycancha.com",
    "spotify": "https://open.spotify.com", "whatsapp": "https://web.whatsapp.com",
    "tradingview": "https://www.tradingview.com", "binance": "https://www.binance.com",
    "instagram": "https://www.instagram.com", "tiktok": "https://www.tiktok.com",
    "claude": "https://claude.ai", "google": "https://www.google.com",
}


def abrir(nombre: str) -> str:
    nombre = nombre.strip(" .").lower()
    url = SITIOS.get(nombre)
    if not url and "." in nombre and " " not in nombre:
        url = nombre if nombre.startswith("http") else f"https://{nombre}"
    if url:
        webbrowser.open(url)
        return f"Abrí {nombre} en el navegador."
    sistema = platform.system()
    try:
        if sistema == "Windows":
            subprocess.Popen(["cmd", "/c", "start", "", nombre])
        elif sistema == "Darwin":
            subprocess.run(["open", "-a", nombre], check=True, capture_output=True)
        elif shutil.which(nombre):
            subprocess.Popen([nombre])
        else:
            return f"No sé abrir '{nombre}'. Agrégalo a SITIOS en alfred/commands/pc.py."
    except Exception:
        return f"No pude abrir '{nombre}'."
    return f"Abriendo {nombre}."


@command("abrir", [r"^(?:abre|abrir|abreme|lanza|inicia) (?:el |la |mi )?(?:pagina de |programa |app (?:de )?)?(.+)$"],
         help="Abre una página o un programa en tu PC.", examples=["abre youtube", "abre easycancha"], priority=25)
def cmd_abrir(ctx, match, texto):
    return abrir(match.group(1))


@command("reservar cancha", [r"\b(?:reserva|reservar|agenda|agendar|arrienda|busca)(?:me)? (?:una )?cancha\b"],
         help="Abre EasyCancha para reservar.", examples=["reserva una cancha"], priority=14)
def reservar_cancha(ctx, match, texto):
    abrir("easycancha")
    return ("Abrí EasyCancha para que elijas la cancha. No puedo reservar por ti porque EasyCancha no "
            "ofrece una conexión para programas. Cuando reserves, dime la fecha y la agrego a tu agenda.")


@tool("abrir_en_pc", "Abre una página web o un programa en el PC del usuario (p. ej. 'youtube', "
      "'easycancha', 'spotify' o una dirección web).", {"nombre": {"type": "string"}})
def t_abrir(ctx, args):
    return abrir(args["nombre"])
