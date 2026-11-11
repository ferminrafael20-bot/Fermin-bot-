"""Jarvis: asistente personal extensible por comandos.

Para añadir un comando nuevo crea un archivo en ``jarvis/commands/`` y decora
una función con ``@command`` (ver ``jarvis/commands/_plantilla.py``).
"""

from .core import Context, Jarvis, command, on_startup

__all__ = ["Jarvis", "Context", "command", "on_startup"]
