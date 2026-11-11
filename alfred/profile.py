"""Tu perfil: lo que Alfred (Claude) debe saber de ti para ayudarte mejor.

Se crea como ``<data_dir>/perfil.md`` la primera vez. Edítalo con cualquier
editor de texto: Claude lo lee en cada conversación.
"""

from pathlib import Path

PLANTILLA = """# Mi perfil para Alfred
(Rellena lo que quieras. Borra las líneas que no apliquen.)

## Sobre mí
- Nombre:
- País y moneda: Chile, peso chileno (CLP)
- Idioma preferido: español

## Mis negocios online
- Tienda Shopify (qué vendo, a quién):
- Influencer con IA (nombre, nicho, redes, objetivo):
- Canal de YouTube faceless (nicho, frecuencia, objetivo):
- Portafolio (qué muestro, a quién):
- Herramientas que uso:
- Metas de este año:

## Perfil de inversor
- Objetivo (ahorro, ingresos, crecimiento, jubilación):
- Horizonte de tiempo (corto <1 año, medio 1-5, largo +5):
- Tolerancia al riesgo (baja, media, alta):
- Experiencia (principiante, intermedio, avanzado):
- Qué ya tengo invertido (cripto, acciones, fondos, forex...):
- Monto aproximado que invierto al mes:
- Cosas que NO quiero (apalancamiento alto, memecoins...):

## Deporte y torneos
- Deporte, club, categoría:
- Torneos que me interesan:

## Clases
- Qué enseño o estudio, y cómo contacto a mis alumnos/profesores:
"""


def path(data_dir: Path) -> Path:
    return Path(data_dir) / "perfil.md"


def load(data_dir: Path) -> str:
    p = path(data_dir)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(PLANTILLA, encoding="utf-8")
    texto = p.read_text(encoding="utf-8")
    return "" if texto.strip() == PLANTILLA.strip() else texto
