"""Cerebro de Alfred con Claude (API de Anthropic).

Cuando ningún comando fijo entiende la frase, Alfred se la pasa a Claude.
Claude conversa en español y puede usar herramientas de Alfred:

* ``registrar_gasto``: anota gastos aunque los digas de forma libre
  ("ayer almorcé con Ana y pagué la mitad de 600").
* ``ejecutar_comando``: ejecuta cualquier comando registrado con ``@command``,
  así que los comandos nuevos que agregues quedan disponibles para Claude
  automáticamente.

Configuración por variables de entorno:
  ANTHROPIC_API_KEY  clave de la API (o un perfil de ``ant auth login``)
  ALFRED_MODEL       modelo (por defecto claude-opus-5-5)
  ALFRED_EFFORT      low | medium | high (por defecto low: respuestas rápidas)
"""

from __future__ import annotations

import json
import os

from .core import Context, registered_commands

DEFAULT_MODEL = "claude-opus-5-5"
MAX_TOOL_ROUNDS = 8

SYSTEM_PROMPT = """Eres Alfred, el asistente personal de tu usuario. Hablas en español, \
con un tono cercano y profesional.

Tus respuestas a menudo se leen en voz alta, así que sé breve (normalmente una a tres \
frases), sin markdown, sin listas largas ni emojis.

Tienes herramientas para actuar en el sistema del usuario:
- registrar_gasto: úsala cada vez que el usuario cuente que gastó o pagó algo, aunque lo \
diga de forma indirecta. Calcula tú el monto si hace falta (por ejemplo, "la mitad de 600" \
son 300). Si un mensaje menciona varios gastos, regístralos todos. Si no está claro el \
monto, pregúntalo en vez de inventarlo.
- ejecutar_comando: ejecuta uno de los comandos de Alfred escribiendo una frase de ejemplo \
de ese comando. Úsala para resúmenes de gastos, reportes, señales de trading, la hora y \
cualquier otra cosa que un comando pueda hacer.

Cuando una herramienta devuelva datos, contéstale al usuario con lo importante en lenguaje \
natural. Las señales de trading son información técnica, no asesoramiento financiero; si el \
usuario te pide que decidas por él una operación, recuérdaselo brevemente."""


def _tools() -> list[dict]:
    from .expenses import CATEGORIAS, OTROS

    catalogo = "\n".join(
        f"- {c.name}: {c.help} Ejemplos: {' | '.join(c.examples) or '—'}"
        for c in registered_commands()
        if c.name not in ("salir", "registrar gasto")
    )
    return [
        {
            "name": "registrar_gasto",
            "description": "Anota un gasto del usuario en su Excel de gastos.",
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "monto": {"type": "number", "description": "Monto gastado, mayor que 0."},
                    "descripcion": {"type": "string",
                                    "description": "Descripción corta en minúsculas, p. ej. 'almuerzo con ana'."},
                    "categoria": {"type": "string", "enum": list(CATEGORIAS) + [OTROS]},
                },
                "required": ["monto", "descripcion", "categoria"],
                "additionalProperties": False,
            },
        },
        {
            "name": "ejecutar_comando",
            "description": ("Ejecuta un comando de Alfred a partir de una frase y devuelve su "
                            "respuesta. Escribe la frase igual que los ejemplos. Comandos "
                            f"disponibles:\n{catalogo}"),
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {"frase": {"type": "string"}},
                "required": ["frase"],
                "additionalProperties": False,
            },
        },
    ]


class ClaudeBrain:
    """Conversación con Claude que conserva el historial durante la sesión."""

    def __init__(self, ctx: Context, run_command, client=None, model: str | None = None,
                 effort: str | None = None):
        if client is None:
            import anthropic
            client = anthropic.Anthropic()
        self.client = client
        self.ctx = ctx
        self.run_command = run_command  # función texto -> respuesta (solo comandos fijos)
        self.model = model or os.environ.get("ALFRED_MODEL", DEFAULT_MODEL)
        self.effort = effort or os.environ.get("ALFRED_EFFORT", "low")
        self.messages: list = []

    def reset(self) -> None:
        self.messages = []

    # ------------------------------------------------------------ tools --
    def _run_tool(self, name: str, args: dict) -> tuple[str, bool]:
        if name == "registrar_gasto":
            from .commands.gastos import _book
            from .expenses import money
            monto = float(args.get("monto", 0))
            if monto <= 0:
                return "El monto debe ser mayor que cero.", True
            exp = _book(self.ctx).add(monto, str(args.get("descripcion", "")).strip() or "sin descripción",
                                      args.get("categoria"), when=self.ctx.now())
            return f"Anotado: {money(exp.monto)} en {exp.categoria} ({exp.descripcion}).", False
        if name == "ejecutar_comando":
            respuesta = self.run_command(str(args.get("frase", "")))
            return respuesta, respuesta.startswith("No entendí")
        return f"Herramienta desconocida: {name}", True

    # ------------------------------------------------------------- chat --
    def ask(self, texto: str) -> str:
        ahora = self.ctx.now()
        self.messages.append({
            "role": "user",
            # la fecha va en el mensaje (no en el system) para no invalidar la caché
            "content": f"[{ahora:%Y-%m-%d %H:%M}] {texto}",
        })
        tools = _tools()

        for _ in range(MAX_TOOL_ROUNDS):
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=self.messages,
                output_config={"effort": self.effort},
                cache_control={"type": "ephemeral"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
            # se guarda el contenido completo (incluye bloques de razonamiento)
            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "refusal":
                return "Lo siento, con eso no puedo ayudarte."
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
