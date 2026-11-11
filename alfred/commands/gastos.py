"""Comandos de gastos: registrar, consultar, borrar y reportes mensuales.

Ejemplos de frases:
  "gasté 25.50 en el súper"          -> Comida
  "pagué 1.200 de renta"             -> Hogar
  "anota gasto de 300 en uber"       -> Transporte
  "gasté 40 en regalo categoría ocio"-> categoría forzada
  "¿cuánto llevo gastado este mes?"
  "reporte del mes" / "reporte de octubre" / "reporte del mes pasado"
"""

import re

from alfred.core import UNKNOWN, command, on_startup
from alfred.expenses import (CATEGORIAS, MESES, OTROS, ExpenseBook, money,
                             parse_expense, summary_text)

VERBOS = (r"^(?:me )?(?:gaste|gasto|pague|compre|invert[ií]|"
          r"(?:anota|apunta|registra|agrega|anade|añade)(?:r)?(?: un)?(?: el)? gasto(?: de)?)\s+(.+)$")


def _book(ctx) -> ExpenseBook:
    if "gastos" not in ctx.extras:
        ctx.extras["gastos"] = ExpenseBook(ctx.data_dir)
    return ctx.extras["gastos"]


def _forced_category(texto: str) -> tuple[str, str | None]:
    m = re.search(r"\s*(?:en la )?categoria\s+(\w+)\s*$", texto)
    if not m:
        return texto, None
    nombre = m.group(1)
    for cat in list(CATEGORIAS) + [OTROS]:
        if cat.lower().replace("ó", "o") == nombre:
            return texto[:m.start()], cat
    return texto[:m.start()], nombre.capitalize()


@command("registrar gasto", [VERBOS],
         help="Anota un gasto en el Excel y lo clasifica por categoría.",
         examples=["gasté 25.50 en el súper", "pagué 1.200 de renta"], priority=20)
def registrar(ctx, match, texto):
    # Frases con varios montos ("300 en comida y 200 en uber") las resuelve Claude
    if ctx.extras.get("brain") and len(re.findall(r"\d+", match.group(1).replace(".", "").replace(",", ""))) > 1:
        return UNKNOWN
    cuerpo, categoria = _forced_category(match.group(1))
    parsed = parse_expense(cuerpo)
    if not parsed:
        return "No encontré el monto. Prueba algo como: 'gasté 20 en comida'."
    monto, descripcion = parsed
    if monto <= 0:
        return "El monto debe ser mayor que cero."
    exp = _book(ctx).add(monto, descripcion, categoria, when=ctx.now())
    return f"Anotado: {money(exp.monto)} en {exp.categoria} ({exp.descripcion})."


def _mes_objetivo(ctx, texto: str) -> tuple[int, int]:
    hoy = ctx.now()
    y, m = hoy.year, hoy.month
    if re.search(r"mes pasado|mes anterior", texto):
        return (y - 1, 12) if m == 1 else (y, m - 1)
    for i, nombre in enumerate(MESES, start=1):
        if re.search(rf"\b{nombre}\b", texto):
            anio = re.search(r"\b(20\d\d)\b", texto)
            if anio:
                return int(anio.group(1)), i
            return (y - 1, i) if i > m else (y, i)  # un mes futuro = año pasado
    return y, m


@command("resumen de gastos",
         [r"\bcuanto (llevo|he|e) gastado\b", r"\b(resumen|total) de (mis )?gastos\b",
          r"\ben que (estoy gastando|he gastado|gasto)\b", r"\bcuanto gaste\b"],
         help="Dice cuánto llevas gastado en el mes y en qué categorías.",
         examples=["¿cuánto llevo gastado este mes?", "¿cuánto gasté en octubre?"],
         priority=30)
def resumen(ctx, match, texto):
    from alfred.core import normalize
    y, m = _mes_objetivo(ctx, normalize(texto))
    book = _book(ctx)
    return summary_text(book.summarize(book.month(y, m)), y, m)


@command("reporte mensual", [r"\b(reporte|informe)\b"],
         help="Genera el Excel de reporte del mes (resumen, gráficos y detalle).",
         examples=["reporte del mes", "reporte de octubre", "reporte del mes pasado"],
         priority=30)
def reporte(ctx, match, texto):
    from alfred.core import normalize
    y, m = _mes_objetivo(ctx, normalize(texto))
    path, s = _book(ctx).build_report(y, m)
    if not path:
        return f"No hay gastos en {MESES[m - 1]} {y}, así que no generé reporte."
    return f"{summary_text(s, y, m)}\nReporte guardado en: {path}"


@command("últimos gastos", [r"\b(ultimos|mis) gastos\b", r"\blista(r)? (de )?gastos\b"],
         help="Muestra los últimos gastos anotados.", examples=["mis últimos gastos"],
         priority=40)
def ultimos(ctx, match, texto):
    items = _book(ctx).all()[-5:]
    if not items:
        return "Todavía no has anotado gastos."
    return "Tus últimos gastos:\n" + "\n".join(
        f"  • {e.fecha:%d/%m} {money(e.monto)} — {e.categoria}: {e.descripcion}" for e in items)


@command("borrar último gasto", [r"\b(borra|elimina|quita|deshaz)(r)? (el )?ultimo gasto\b"],
         help="Borra el último gasto (por si te equivocaste).",
         examples=["borra el último gasto"], priority=10)
def borrar(ctx, match, texto):
    exp = _book(ctx).delete_last()
    if not exp:
        return "No hay gastos para borrar."
    return f"Borrado: {money(exp.monto)} — {exp.descripcion}."


@command("categorías", [r"\bcategorias\b"],
         help="Lista las categorías disponibles.", examples=["¿qué categorías hay?"],
         priority=45)
def categorias(ctx, match, texto):
    return "Categorías: " + ", ".join(list(CATEGORIAS) + [OTROS]) + "."


@on_startup
def reporte_automatico(ctx):
    """Al arrancar, si terminó un mes con gastos y aún no tiene reporte, lo crea."""
    hoy = ctx.now()
    y, m = (hoy.year - 1, 12) if hoy.month == 1 else (hoy.year, hoy.month - 1)
    book = _book(ctx)
    if book.report_path(y, m).exists() or not book.month(y, m):
        return None
    path, s = book.build_report(y, m)
    return f"Terminó {MESES[m - 1]}. Te preparé el reporte:\n{summary_text(s, y, m)}\nArchivo: {path}"
