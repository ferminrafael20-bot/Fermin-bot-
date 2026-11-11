"""Notas e ideas (por ejemplo, ideas para tus negocios o videos).

Ejemplos: "guarda la idea video sobre 5 herramientas de IA gratis",
"nota: llamar al proveedor", "mis ideas", "mis notas".
"""

from alfred.core import command, original_text, tool


def _path(ctx):
    return ctx.data_dir / "notas.md"


def guardar(ctx, texto: str, tema: str = "") -> str:
    tema = f"[{tema}] " if tema else ""
    with _path(ctx).open("a", encoding="utf-8") as f:
        f.write(f"- {ctx.now():%Y-%m-%d %H:%M} {tema}{texto.strip()}\n")
    return "Guardado en tus notas."


@command("guardar nota", [r"^(?:guarda|anota|apunta|guardame)(?:r)? (?:la |una |esta )?(idea|nota)[:,]? (.+)$",
                          r"^(nota|idea)[:,] (.+)$"],
         help="Guarda una nota o idea.", examples=["guarda la idea video de 5 IAs gratis"], priority=18)
def guardar_nota(ctx, match, texto):
    return guardar(ctx, original_text(texto, match.group(2)), "idea" if match.group(1) == "idea" else "")


@command("ver notas", [r"^(?:mis|ver|muestrame mis) (notas|ideas)$"],
         help="Muestra tus últimas notas.", examples=["mis notas"], priority=40)
def ver_notas(ctx, match, texto):
    if not _path(ctx).exists():
        return "Aún no tienes notas."
    lineas = _path(ctx).read_text(encoding="utf-8").splitlines()
    if match.group(1) == "ideas":
        lineas = [x for x in lineas if "[idea]" in x]
    return "Tus últimas notas:\n" + "\n".join(lineas[-10:]) if lineas else "Aún no tienes ideas guardadas."


@tool("guardar_nota", "Guarda una nota o idea del usuario en su archivo de notas.",
      {"texto": {"type": "string"},
       "tema": {"type": "string", "description": "Tema corto (p. ej. 'youtube', 'influencer', 'idea') o vacío."}})
def t_guardar_nota(ctx, args):
    return guardar(ctx, args["texto"], args.get("tema", ""))


@tool("leer_notas", "Devuelve las notas guardadas del usuario (las últimas 50).", {})
def t_leer_notas(ctx, args):
    if not _path(ctx).exists():
        return "No hay notas."
    return "\n".join(_path(ctx).read_text(encoding="utf-8").splitlines()[-50:])
