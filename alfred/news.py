"""Resumen diario de noticias de cripto, forex y acciones (Claude + búsqueda web)."""

from __future__ import annotations

from datetime import datetime

from .agenda import fecha_humana

PROMPT = """Hoy es {fecha}. Busca en la web las noticias más relevantes de las últimas 24 horas \
para un inversor y trader en tres áreas: criptomonedas (en especial BTC, SOL, XRP), forex \
(dólar, euro, oro/XAU y en especial el dólar en Chile, USD/CLP, junto con el cobre) y bolsa de valores (índices de EE. UU., grandes tecnológicas, datos \
macro y decisiones de bancos centrales, incluido el Banco Central de Chile y el IPSA cuando \
haya novedades).

Escribe un correo en español, en texto plano (sin markdown), con este formato:

Resumen en 3 líneas: lo más importante del día.

CRIPTO
- 3 a 5 noticias, cada una en 1-2 frases con por qué importa.

FOREX
- 2 a 4 noticias.

ACCIONES
- 3 a 5 noticias.

AGENDA DE HOY
- Datos económicos o eventos importantes que se publican hoy, con hora si la conoces.

No inventes cifras: si no estás seguro de un dato, no lo pongas. Es información, no \
recomendación de inversión."""

WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 10}


def build_digest(brain, now: datetime) -> str:
    """Pide a Claude el resumen usando búsqueda web. Devuelve el texto con fuentes."""
    messages = [{"role": "user", "content": PROMPT.format(fecha=fecha_humana(now).split(" a las")[0])}]
    fuentes: dict[str, str] = {}
    texto = ""
    for _ in range(6):
        resp = brain.client.beta.messages.create(
            model=brain.model, max_tokens=16000, tools=[WEB_SEARCH], messages=messages,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        )
        for b in resp.content:
            if b.type == "text":
                texto += b.text
                for c in getattr(b, "citations", None) or []:
                    url = getattr(c, "url", None)
                    if url:
                        fuentes.setdefault(url, getattr(c, "title", "") or url)
        if resp.stop_reason == "refusal":
            raise RuntimeError("Claude no pudo preparar el resumen.")
        if resp.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": resp.content})  # continuar la búsqueda
    texto = texto.strip()
    if fuentes:
        texto += "\n\nFUENTES\n" + "\n".join(f"- {t}: {u}" for u, t in list(fuentes.items())[:15])
    return texto + "\n\n— Alfred"
