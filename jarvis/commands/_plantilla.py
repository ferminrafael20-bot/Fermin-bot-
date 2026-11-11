"""PLANTILLA para crear un comando nuevo.

1. Copia este archivo dentro de jarvis/commands/ con otro nombre, SIN el
   guion bajo inicial (p. ej. ``clima.py``). Se cargará solo al arrancar.
2. Cambia el nombre, los patrones y la lógica.

Los patrones se comparan contra el texto en minúsculas y sin tildes,
así que escribe "cuanto" en vez de "cuánto".
"""

from jarvis.core import command


@command(
    name="mi_comando",
    patterns=[r"^di algo bonito$"],
    help="Ejemplo de comando nuevo.",
    examples=["di algo bonito"],
)
def mi_comando(ctx, match, texto):
    # ctx.now()      -> fecha/hora actual
    # ctx.data_dir   -> carpeta donde guardar archivos
    # match.group(1) -> partes capturadas por el patrón
    return "Hoy vas a tener un gran día."
