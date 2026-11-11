"""Alfred: asistente personal extensible por comandos.

Para añadir un comando nuevo crea un archivo en ``alfred/commands/`` y decora
una función con ``@command`` (ver ``alfred/commands/_plantilla.py``).
"""

from .core import Context, Alfred, command, on_startup

__all__ = ["Alfred", "Context", "command", "on_startup"]
