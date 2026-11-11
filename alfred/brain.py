"""Cerebro de Alfred con Claude (API de Anthropic).

Cuando ningún comando fijo entiende la frase, Alfred se la pasa a Claude.
Claude conversa en español, lee tu perfil (datos_alfred/perfil.md), puede
buscar en internet y usa las herramientas de Alfred:

* las registradas con ``@tool`` en los módulos de ``alfred/commands``
  (gastos, agenda, notas, archivos, tienda, PC...);
* ``ejecutar_comando``: cualquier comando registrado con ``@command``.

Así, lo que agregues a Alfred queda disponible para Claude automáticamente.

Configuración por variables de entorno:
  ANTHROPIC_API_KEY  clave de la API (o un perfil de ``ant auth login``)
  ALFRED_MODEL       modelo (por defecto claude-opus-5-5)
  ALFRED_EFFORT      low | medium | high (por defecto low: respuestas rápidas)
"""

from __future__ import annotations

import json
import os

from . import profile
from .core import Context, registered_commands, registered_tools

DEFAULT_MODEL = "claude-opus-5-5"
MAX_ROUNDS = 10
WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 5}

SYSTEM_PROMPT = """Eres Alfred, el asistente personal de tu usuario, al estilo de un mayordomo \
eficiente y cercano. Hablas en español.

El usuario vive en Chile: los montos son en pesos chilenos (CLP, sin decimales, con punto \
de miles: $15.990) y entiendes modismos chilenos ("lucas" = miles de pesos, "un palo" = un \
millón, bencina, micro, once, carrete). Si habla de otra moneda, conviértela o pregunta.

Tus respuestas a menudo se leen en voz alta o en el celular, así que sé breve (normalmente \
una a tres frases), sin markdown ni listas largas, salvo que el usuario pida algo extenso \
como un guion, un plan o un análisis.

Cómo actuar:
- Usa las herramientas para hacer las cosas en vez de explicar cómo hacerlas. Si el usuario \
cuenta que gastó algo, regístralo. Si menciona una clase, torneo, cita o algo que recordar, \
agéndalo con crear_evento (las fechas que recibes y escribes son hora local; la fecha y \
hora actuales vienen al inicio de cada mensaje del usuario).
- Si falta un dato imprescindible (monto, fecha, hora), pregúntalo en vez de inventarlo.
- Algunas herramientas dejan una acción pendiente de confirmación (organizar archivos, \
cambios en la tienda). En ese caso explica qué se hará y pide que responda "sí".
- Usa web_search para datos actuales: precios, noticias, resultados, horarios.
- ejecutar_comando sirve para todo lo demás que Alfred sabe hacer (resúmenes y reportes de \
gastos, señales de trading, hora, etc.).

Negocios online: ayuda con la tienda Shopify, el influencer con IA, el canal de YouTube \
faceless y el portafolio con ideas concretas, guiones, títulos, descripciones, SEO, \
calendarios de contenido y estrategias de crecimiento y monetización. Puedes guardar ideas \
con guardar_nota.

Inversiones: puedes orientar según el perfil de inversor del usuario (objetivo, horizonte, \
tolerancia al riesgo): explica opciones, riesgos, costos y diversificación, y propone \
alternativas acordes a su perfil, considerando opciones disponibles en Chile cuando \
corresponda (por ejemplo depósitos a plazo, fondos mutuos, APV, ETFs, acciones o cripto) y \
el efecto del tipo de cambio USD/CLP. Aclara brevemente que es información educativa y no \
asesoría financiera profesional, nunca prometas rendimientos y desaconseja arriesgar dinero \
que no pueda perder. Si su perfil de inversor está vacío, hazle primero 3 o 4 preguntas \
cortas y sugiérele guardarlo en su perfil. Las señales de trading de Alfred son técnicas, no \
una garantía."""


def _command_tool() -> dict:
    catalogo = "\n".join(
        f"- {c.name}: {c.help} Ejemplos: {' | '.join(c.examples) or '—'}"
        for c in registered_commands()
        if c.name not in ("salir", "registrar gasto", "confirmar", "cancelar")
    )
    return {
        "name": "ejecutar_comando",
        "description": ("Ejecuta un comando de Alfred a partir de una frase y devuelve su respuesta. "
                        f"Escribe la frase igual que los ejemplos. Comandos disponibles:\n{catalogo}"),
        "strict": True,
        "input_schema": {"type": "object", "properties": {"frase": {"type": "string"}},
                         "required": ["frase"], "additionalProperties": False},
    }


def build_tools() -> list[dict]:
    tools = []
    for t in sorted(registered_tools(), key=lambda t: t.name):  # orden fijo: favorece la caché
        d = {"name": t.name, "description": t.description, "input_schema": t.schema}
        if t.strict:
            d["strict"] = True
        tools.append(d)
    return tools + [_command_tool(), WEB_SEARCH]


class ClaudeBrain:
    """Conversación con Claude que conserva el historial durante la sesión."""

    def __init__(self, ctx: Context, run_command, client=None, model: str | None = None,
                 effort: str | None = None):
        if client is None:
            import anthropic
            client = anthropic.Anthropic()
        self.client = client
        self.ctx = ctx
        self.run_command = run_command  # texto -> respuesta (solo comandos fijos)
        self.model = model or os.environ.get("ALFRED_MODEL", DEFAULT_MODEL)
        self.effort = effort or os.environ.get("ALFRED_EFFORT", "low")
        self.messages: list = []

    def reset(self) -> None:
        self.messages = []

    def _system(self) -> list[dict]:
        bloques = [{"type": "text", "text": SYSTEM_PROMPT}]
        perfil = profile.load(self.ctx.data_dir)
        bloques.append({"type": "text", "text": "Perfil del usuario:\n" + perfil if perfil else
                        "El usuario aún no rellenó su perfil (archivo perfil.md en su carpeta de datos)."})
        return bloques

    def _run_tool(self, name: str, args: dict) -> tuple[str, bool]:
        if name == "ejecutar_comando":
            respuesta = self.run_command(str(args.get("frase", "")))
            return respuesta, respuesta.startswith("No entendí")
        for t in registered_tools():
            if t.name == name:
                return str(t.fn(self.ctx, args)), False
        return f"Herramienta desconocida: {name}", True

    def ask(self, texto: str) -> str:
        ahora = self.ctx.now()
        self.messages.append({
            "role": "user",
            # la fecha va en el mensaje (no en el system) para no invalidar la caché
            "content": f"[{ahora:%Y-%m-%d %H:%M}, {['lunes','martes','miércoles','jueves','viernes','sábado','domingo'][ahora.weekday()]}] {texto}",
        })
        tools, system = build_tools(), self._system()

        for _ in range(MAX_ROUNDS):
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                system=system,
                tools=tools,
                messages=self.messages,
                output_config={"effort": self.effort},
                cache_control={"type": "ephemeral"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
            # se guarda el contenido completo (incluye razonamiento y búsquedas)
            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "refusal":
                return "Lo siento, con eso no puedo ayudarte."
            if response.stop_reason == "pause_turn":
                continue  # búsqueda web larga: se retoma
            if response.stop_reason != "tool_use":
                texto_resp = "".join(b.text for b in response.content if b.type == "text").strip()
                return texto_resp or "Listo."

            resultados = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                try:
                    args = block.input if isinstance(block.input, dict) else json.loads(block.input)
                    salida, es_error = self._run_tool(block.name, args)
                except Exception as exc:
                    salida, es_error = f"Error: {exc}", True
                resultados.append({"type": "tool_result", "tool_use_id": block.id,
                                   "content": salida, "is_error": es_error})
            self.messages.append({"role": "user", "content": resultados})

        return "Me enredé con esa petición. ¿Me la repites de otra forma?"


def claude_available() -> bool:
    """True si el SDK está instalado y hay credenciales configuradas."""
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    if os.environ.get("ALFRED_CLAUDE", "").lower() in ("0", "no", "off"):
        return False
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
                or os.environ.get("ANTHROPIC_PROFILE")
                or os.path.isdir(os.path.expanduser("~/.config/anthropic")))
