"""Organizar archivos.

Ejemplos: "organiza mis descargas", "organiza el escritorio por fecha",
"organiza la carpeta C:\\Users\\yo\\Proyectos", "deshaz la organización",
"archivos más grandes de descargas".
Siempre te muestra el plan y espera tu "sí" antes de mover nada.
"""

import re

from alfred import files
from alfred.core import ask_confirmation, command, tool

_ALIAS_RE = "|".join(files.ALIAS)


def _carpeta(match_text: str, original: str):
    m = re.search(r"carpeta\s+([A-Za-z]:\\.+|/.+|~.*)$", original.strip(" ¿?¡!"))
    if m:
        return files.resolve_folder(m.group(1).strip('"\' '))
    m = re.search(rf"\b({_ALIAS_RE})\b", match_text)
    return files.resolve_folder(m.group(1)) if m else None


def proponer(ctx, folder, modo: str) -> str:
    moves = files.plan(folder, modo)
    if not moves:
        return f"{folder} ya está ordenada: no hay archivos sueltos."
    log_dir = ctx.data_dir / "organizacion"

    def ejecutar():
        n, _ = files.apply(moves, log_dir)
        return f"Listo, moví {n} archivos en {folder}. Si no te gusta, di 'deshaz la organización'."

    return ask_confirmation(ctx, f"En {folder} hay {len(moves)} archivos sueltos. Los movería así: "
                                 f"{files.summary(moves)}.", ejecutar)


@command("organizar archivos", [r"\b(?:organiza|ordena|limpia)(?:r|me)?\b.*\b(?:carpeta|archivos|" + _ALIAS_RE + r")\b"],
         help="Ordena una carpeta en subcarpetas por tipo (o por fecha). Pide confirmación.",
         examples=["organiza mis descargas", "organiza el escritorio por fecha"], priority=20)
def organizar(ctx, match, texto):
    folder = _carpeta(match.string, texto)
    if not folder:
        return "No encontré esa carpeta. Prueba 'organiza mis descargas' o 'organiza la carpeta <ruta>'."
    return proponer(ctx, folder, "fecha" if "fecha" in match.string else "tipo")


@command("deshacer organización", [r"\b(?:deshaz|deshacer|revierte|revertir)\b.*\borganiza"],
         help="Devuelve los archivos a donde estaban.", examples=["deshaz la organización"], priority=10)
def deshacer(ctx, match, texto):
    n = files.undo_last(ctx.data_dir / "organizacion")
    return "No hay ninguna organización para deshacer." if n is None else f"Devolví {n} archivos a su lugar."


@command("archivos grandes", [r"\barchivos (?:mas )?(?:grandes|pesados)\b"],
         help="Muestra los archivos que más espacio ocupan.", examples=["archivos más grandes de descargas"],
         priority=30)
def grandes(ctx, match, texto):
    folder = _carpeta(match.string, texto) or files.resolve_folder("descargas")
    if not folder:
        return "Dime en qué carpeta: 'archivos más grandes de descargas'."
    lista = files.large_files(folder)
    if not lista:
        return "No encontré archivos."
    return f"Los más grandes en {folder}:\n" + "\n".join(
        f"  • {f.name}: {size / 1e6:,.1f} MB" for f, size in lista)


@tool("organizar_carpeta",
      "Propone ordenar una carpeta del PC en subcarpetas. No mueve nada hasta que el usuario diga 'sí'. "
      "carpeta: 'descargas', 'escritorio', 'documentos', 'imagenes', 'videos', 'musica' o una ruta completa.",
      {"carpeta": {"type": "string"}, "modo": {"type": "string", "enum": ["tipo", "fecha"]}})
def t_organizar(ctx, args):
    folder = files.resolve_folder(args["carpeta"].lower()) or files.resolve_folder(args["carpeta"])
    if not folder:
        return "No existe esa carpeta."
    return proponer(ctx, folder, args["modo"]) + "\n(Dile al usuario que responda 'sí' para confirmar.)"
