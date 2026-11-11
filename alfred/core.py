"""Núcleo de Alfred: registro de comandos, contexto y despacho.

Cada comando se registra con el decorador ``@command`` indicando una o más
expresiones regulares. Alfred normaliza lo que dices (minúsculas, sin tildes,
sin la palabra "alfred" al inicio) y ejecuta el primer comando cuyo patrón
coincida, por orden de prioridad.
"""

from __future__ import annotations

import importlib
import os
import threading
import pkgutil
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

Handler = Callable[["Context", re.Match, str], str]
StartupHook = Callable[["Context"], "str | None"]


def normalize(text: str) -> str:
    """Minúsculas, sin tildes, sin signos sobrantes y sin el nombre 'alfred'."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower().strip()
    text = re.sub(r"[¿?¡!]", "", text)
    text = re.sub(r"^(oye\s+|hey\s+)?alfred(?:o)?[\s,:.]*", "", text)
    return re.sub(r"\s+", " ", text).strip(" .")


def original_text(original: str, fragment: str) -> str:
    """Recupera del texto original (con tildes y mayúsculas) el fragmento
    normalizado ``fragment``. Si no lo encuentra, devuelve ``fragment``."""
    if not fragment:
        return fragment
    words = original.split()
    norm = [normalize(w).strip(",.;:") for w in words]
    target = [w.strip(",.;:") for w in fragment.split()]
    for i in range(len(words) - len(target) + 1):
        if norm[i:i + len(target)] == target:
            return " ".join(words[i:i + len(target)]).strip("¿?¡!,.;: ")
    return fragment


@dataclass
class Command:
    name: str
    patterns: list[re.Pattern]
    handler: Handler
    help: str = ""
    examples: tuple[str, ...] = ()
    priority: int = 50


_REGISTRY: list[Command] = []
_STARTUP_HOOKS: list[StartupHook] = []


def command(name: str, patterns: list[str] | str, help: str = "",
            examples: tuple[str, ...] | list[str] = (), priority: int = 50):
    """Registra una función como comando de Alfred.

    La función recibe ``(ctx, match, texto_original)`` y devuelve la respuesta
    (texto) que Alfred dirá. Los patrones se comparan contra el texto
    normalizado (minúsculas y sin tildes). Menor ``priority`` = se prueba antes.
    """
    if isinstance(patterns, str):
        patterns = [patterns]

    def decorator(fn: Handler) -> Handler:
        _REGISTRY[:] = [c for c in _REGISTRY if c.name != name]  # recarga segura
        _REGISTRY.append(Command(name, [re.compile(p) for p in patterns], fn,
                                 help, tuple(examples), priority))
        _REGISTRY.sort(key=lambda c: c.priority)
        return fn

    return decorator


def on_startup(fn: StartupHook) -> StartupHook:
    """Registra una función que se ejecuta al arrancar Alfred (p. ej. reportes)."""
    if fn not in _STARTUP_HOOKS:
        _STARTUP_HOOKS.append(fn)
    return fn


def registered_commands() -> list[Command]:
    return list(_REGISTRY)


# ------------------------------------------------- herramientas para Claude --

@dataclass
class Tool:
    name: str
    description: str
    schema: dict
    fn: Callable[["Context", dict], str]
    strict: bool = True


_TOOLS: dict[str, Tool] = {}


def tool(name: str, description: str, properties: dict, required: list[str] | None = None):
    """Registra una función como herramienta que Claude puede usar.

    La función recibe ``(ctx, args)`` y devuelve un texto con el resultado.
    Si lanza una excepción, Claude recibe el error y puede reintentar.
    """
    required = list(properties) if required is None else required

    def decorator(fn):
        schema = {"type": "object", "properties": properties,
                  "required": required, "additionalProperties": False}
        _TOOLS[name] = Tool(name, description, schema, fn,
                            strict=set(required) == set(properties))
        return fn

    return decorator


def registered_tools() -> list[Tool]:
    return list(_TOOLS.values())


def ask_confirmation(ctx: "Context", description: str, action: Callable[[], str]) -> str:
    """Deja una acción pendiente hasta que el usuario diga "sí"."""
    ctx.extras["pendiente"] = (description, action)
    return f"{description}\n¿Lo hago? Di 'sí' para confirmar o 'no' para cancelar."


def load_env(*paths: Path) -> None:
    """Carga variables de archivos .env (sin pisar las ya definidas)."""
    for path in paths:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_commands() -> None:
    """Importa todos los módulos de ``alfred/commands`` (descubrimiento automático)."""
    from . import commands as pkg

    for mod in pkgutil.iter_modules(pkg.__path__):
        if not mod.name.startswith("_"):
            importlib.import_module(f"{pkg.__name__}.{mod.name}")


@dataclass
class Context:
    """Estado compartido que reciben los comandos."""

    data_dir: Path
    clock: Callable[[], datetime] = datetime.now
    should_exit: bool = False
    extras: dict = field(default_factory=dict)  # espacio libre para tus comandos

    def now(self) -> datetime:
        return self.clock()


def default_data_dir() -> Path:
    return Path(os.environ.get("ALFRED_DATA_DIR", "datos_alfred")).expanduser()


UNKNOWN = "No entendí ese comando. Di 'ayuda' para ver lo que sé hacer."


class Alfred:
    """Asistente. Si se le pasa un ``brain`` (p. ej. Claude), le envía lo que
    ningún comando fijo entiende. ``brain=True`` lo crea con la configuración
    por defecto; ``None`` lo activa solo si hay credenciales de Anthropic."""

    def __init__(self, data_dir: Path | str | None = None,
                 clock: Callable[[], datetime] = datetime.now, brain=None):
        load_env(Path.cwd() / ".env")
        load_commands()
        path = Path(data_dir) if data_dir else default_data_dir()
        path.mkdir(parents=True, exist_ok=True)
        load_env(path / ".env")
        self.ctx = Context(data_dir=path, clock=clock)
        self.lock = threading.RLock()  # comandos y tareas programadas no se pisan
        self.brain = None
        if brain is None or brain is True:
            from .brain import ClaudeBrain, claude_available
            if brain is True or claude_available():
                self.brain = ClaudeBrain(self.ctx, self.run_command)
        elif brain is not False:
            self.brain = brain
        self.ctx.extras["brain"] = self.brain

    def startup(self) -> list[str]:
        """Ejecuta las tareas de arranque y devuelve los mensajes que generen."""
        messages = []
        for hook in _STARTUP_HOOKS:
            try:
                msg = hook(self.ctx)
            except Exception as exc:  # una tarea rota no debe impedir arrancar
                msg = f"Error en tarea de inicio {hook.__name__}: {exc}"
            if msg:
                messages.append(msg)
        return messages

    def handle(self, text: str) -> str:
        """Comandos fijos primero (rápidos y sin costo); si no, Claude."""
        if not normalize(text):
            return "¿Sí? Dime qué necesitas."
        with self.lock:
            respuesta = self.run_command(text)
            if respuesta is not UNKNOWN or self.brain is None:
                return respuesta
            try:
                return self.brain.ask(text)
            except Exception as exc:
                return f"No pude hablar con Claude ({type(exc).__name__}: {exc})."

    def run_command(self, text: str) -> str:
        """Ejecuta solo los comandos fijos (sin Claude)."""
        clean = normalize(text)
        for cmd in _REGISTRY:
            for pattern in cmd.patterns:
                match = pattern.search(clean)
                if match:
                    try:
                        return cmd.handler(self.ctx, match, text)
                    except Exception as exc:
                        return f"Tuve un problema con '{cmd.name}': {exc}"
        return UNKNOWN

    @property
    def should_exit(self) -> bool:
        return self.ctx.should_exit
