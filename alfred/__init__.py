"""Alfred: asistente personal extensible por comandos.

Para añadir un comando nuevo crea un archivo en ``alfred/commands/`` y decora
una función con ``@command`` (ver ``alfred/commands/_plantilla.py``).
"""

from .core import Alfred, Context, ask_confirmation, command, on_startup, tool

__all__ = ["Alfred", "Context", "command", "tool", "on_startup", "ask_confirmation"]
