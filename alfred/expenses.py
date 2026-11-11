"""Libro de gastos en Excel y generación de reportes mensuales.

Los gastos se guardan en ``<data_dir>/gastos.xlsx`` (hoja "Gastos"), así que
puedes abrir el archivo con Excel cuando quieras. Los reportes mensuales se
crean como ``<data_dir>/reportes/reporte_AAAA-MM.xlsx``.
"""

from __future__ import annotations

import os
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.styles import Font, PatternFill

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

HEADERS = ["Fecha", "Hora", "Monto", "Categoría", "Descripción"]

# Palabras clave -> categoría. Amplía esta lista a tu gusto (sin tildes).
CATEGORIAS: dict[str, list[str]] = {
    "Comida": ["jumbo", "lider", "unimarc", "santa isabel", "tottus", "acuenta", "completo", "empanada", "sushi", "colacion", "minimarket", "botilleria", "pedidosya", "justo", "cornershop", "comida", "super", "supermercado", "mercado", "restaurante", "almuerzo",
               "cena", "desayuno", "cafe", "pizza", "hamburguesa", "tacos", "pan",
               "panaderia", "frutas", "verduras", "carniceria", "delivery", "rappi",
               "uber eats", "pedidos ya", "snack", "bebida"],
    "Transporte": ["bencina", "copec", "shell", "petrobras", "aramco", "micro", "colectivo", "bip", "tag", "autopista", "red movilidad", "efe", "turbus", "pullman", "permiso de circulacion", "revision tecnica", "soap", "gasolina", "nafta", "combustible", "uber", "taxi", "didi", "cabify",
                   "bus", "autobus", "metro", "pasaje", "peaje", "estacionamiento",
                   "parqueo", "parking", "mecanico", "carro", "auto", "moto"],
    "Hogar": ["gastos comunes", "contribuciones", "sodimac", "easy", "homecenter", "lavanderia", "renta", "alquiler", "arriendo", "hipoteca", "muebles", "limpieza",
              "ferreteria", "casa"],
    "Servicios": ["enel", "cge", "aguas andinas", "esval", "metrogas", "lipigas", "abastible", "gasco", "entel", "movistar", "wom", "claro", "vtr", "mundo", "gtd", "icloud", "google one", "chatgpt", "claude", "youtube premium", "luz", "agua", "gas", "internet", "telefono", "celular", "cable",
                  "netflix", "spotify", "suscripcion", "electricidad", "plan"],
    "Salud": ["isapre", "fonasa", "cruz verde", "salcobrand", "ahumada", "dr simi", "clinica", "examen", "kine", "kinesiologo", "psicologo", "optica", "lentes", "farmacia", "medicina", "medicamento", "doctor", "medico", "dentista",
              "hospital", "consulta", "seguro medico", "gimnasio", "gym"],
    "Ocio": ["copete", "carrete", "piscola", "entrada", "estadio", "pádel", "padel", "cancha", "easycancha", "torneo", "cine", "fiesta", "bar", "cerveza", "trago", "concierto", "juego",
             "videojuego", "viaje", "hotel", "salida", "paseo"],
    "Compras": ["falabella", "paris", "ripley", "mercado libre", "aliexpress", "temu", "shein", "hites", "la polar", "ropa", "zapatos", "tenis", "amazon", "regalo", "tienda", "shopping",
                "electronica", "accesorio"],
    "Educación": ["colegiatura", "arancel", "preu", "udemy", "platzi", "coursera", "curso", "libro", "colegio", "escuela", "universidad", "matricula",
                  "clase", "utiles"],
    "Finanzas": ["afp", "apv", "deposito a plazo", "fondo mutuo", "cuota", "credito", "linea de credito", "avance", "seguro", "tarjeta", "prestamo", "deuda", "banco", "comision", "inversion",
                 "ahorro", "cripto"],
}
OTROS = "Otros"


@dataclass
class Expense:
    fecha: date
    hora: str
    monto: float
    categoria: str
    descripcion: str


# ----------------------------------------------------------------- parseo ---

_MULTIPLIERS = {"mil": 1_000, "k": 1_000, "luca": 1_000, "lucas": 1_000,
                "millon": 1_000_000, "millones": 1_000_000, "palo": 1_000_000, "palos": 1_000_000}
_AMOUNT_RE = re.compile(
    r"(?:\$|usd|us\$|€)?\s*(\d[\d.,]*)\s*(mil|k|lucas?|millon|millones|palos?)?\b"
)


def parse_number(raw: str) -> float:
    """Convierte '1.200', '1,200.50', '25,5' o '25.50' en número.

    Regla: si hay "." y "," a la vez, el último separador es el decimal. Si
    hay uno solo seguido de exactamente 3 dígitos, es separador de miles.
    """
    raw = raw.strip(".,")
    if "." in raw and "," in raw:
        dec = "." if raw.rfind(".") > raw.rfind(",") else ","
        thou = "," if dec == "." else "."
        return float(raw.replace(thou, "").replace(dec, "."))
    for sep in (".", ","):
        if sep in raw:
            parts = raw.split(sep)
            if len(parts) > 2 or len(parts[1]) == 3:  # 1.200 / 1.200.000
                return float(raw.replace(sep, ""))
            return float(raw.replace(sep, "."))      # 25.50 / 25,5
    return float(raw)


def parse_expense(texto: str) -> tuple[float, str] | None:
    """Extrae (monto, descripción) de algo como '25.50 en el super'."""
    texto = re.sub(r"\b(?:una|un) (luca|palo)\b", r"1 \1", texto)  # "una luca" = 1.000
    m = _AMOUNT_RE.search(texto)
    if not m:
        return None
    monto = parse_number(m.group(1)) * _MULTIPLIERS.get(m.group(2) or "", 1)
    resto = (texto[:m.start()] + " " + texto[m.end():]).strip()
    resto = re.sub(r"^(pesos|dolares|euros|soles|bolivares|lempiras|quetzales|usd|\$)\s+", "", resto)
    resto = re.sub(r"^(en|de|del|para|por)\s+(el|la|los|las|un|una|unos|unas)?\s*", "", resto)
    return monto, resto.strip() or "sin descripción"


def categorize(descripcion: str) -> str:
    """Asigna una categoría según palabras clave (primera coincidencia)."""
    from .core import normalize
    desc = f" {normalize(descripcion)} "
    for categoria, palabras in CATEGORIAS.items():
        if categoria.lower() in desc:
            return categoria
        for palabra in palabras:
            if re.search(rf"\b{re.escape(palabra)}s?\b", desc):
                return categoria
    return OTROS


def currency() -> str:
    """Moneda configurada (ALFRED_MONEDA). Por defecto peso chileno."""
    return os.environ.get("ALFRED_MONEDA", "CLP").upper()


def _sin_decimales() -> bool:
    return currency() in ("CLP", "COP", "PYG", "JPY", "KRW")


def money(x: float) -> str:
    """$15.990 en pesos chilenos; $15,990.00 en otras monedas."""
    if _sin_decimales():
        return "$" + f"{x:,.0f}".replace(",", ".")
    return f"${x:,.2f}"


def excel_format() -> str:
    return '"$"#,##0' if _sin_decimales() else "#,##0.00"


# ----------------------------------------------------------------- libro ----

class ExpenseBook:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.path = self.data_dir / "gastos.xlsx"
        self.reports_dir = self.data_dir / "reportes"

    def _open(self):
        if self.path.exists():
            return load_workbook(self.path)
        wb = Workbook()
        ws = wb.active
        ws.title = "Gastos"
        ws.append(HEADERS)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F4E78")
        for col, width in zip("ABCDE", (12, 8, 12, 14, 40)):
            ws.column_dimensions[col].width = width
        ws.freeze_panes = "A2"
        return wb

    def add(self, monto: float, descripcion: str, categoria: str | None = None,
            when: datetime | None = None) -> Expense:
        when = when or datetime.now()
        exp = Expense(when.date(), when.strftime("%H:%M"), round(monto, 2),
                      categoria or categorize(descripcion), descripcion)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        wb = self._open()
        ws = wb["Gastos"]
        ws.append([exp.fecha, exp.hora, exp.monto, exp.categoria, exp.descripcion])
        ws.cell(ws.max_row, 1).number_format = "DD/MM/YYYY"
        ws.cell(ws.max_row, 3).number_format = excel_format()
        self._save(wb)
        return exp

    def _save(self, wb) -> None:
        try:
            wb.save(self.path)
        except PermissionError:
            raise RuntimeError("el archivo gastos.xlsx está abierto en Excel; ciérralo y repíteme el gasto") from None

    def all(self) -> list[Expense]:
        if not self.path.exists():
            return []
        ws = load_workbook(self.path, read_only=True)["Gastos"]
        out = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or row[0] is None or row[2] is None:
                continue
            fecha = row[0].date() if isinstance(row[0], datetime) else row[0]
            out.append(Expense(fecha, str(row[1] or ""), float(row[2]),
                               str(row[3] or OTROS), str(row[4] or "")))
        return out

    def month(self, year: int, month: int) -> list[Expense]:
        return [e for e in self.all() if e.fecha.year == year and e.fecha.month == month]

    def delete_last(self) -> Expense | None:
        items = self.all()
        if not items:
            return None
        wb = self._open()
        ws = wb["Gastos"]
        ws.delete_rows(len(items) + 1)
        self._save(wb)
        return items[-1]

    # ------------------------------------------------------------- reporte --

    @staticmethod
    def summarize(items: list[Expense]) -> dict:
        por_cat: dict[str, float] = defaultdict(float)
        por_dia: dict[date, float] = defaultdict(float)
        for e in items:
            por_cat[e.categoria] += e.monto
            por_dia[e.fecha] += e.monto
        total = sum(por_cat.values())
        return {
            "total": total,
            "n": len(items),
            "por_categoria": dict(sorted(por_cat.items(), key=lambda kv: -kv[1])),
            "por_dia": dict(sorted(por_dia.items())),
            "mayor": max(items, key=lambda e: e.monto) if items else None,
        }

    def report_path(self, year: int, month: int) -> Path:
        return self.reports_dir / f"reporte_{year}-{month:02d}.xlsx"

    def build_report(self, year: int, month: int) -> tuple[Path | None, dict]:
        items = self.month(year, month)
        s = self.summarize(items)
        if not items:
            return None, s

        wb = Workbook()
        bold = Font(bold=True)
        head_fill = PatternFill("solid", fgColor="1F4E78")
        head_font = Font(bold=True, color="FFFFFF")

        ws = wb.active
        ws.title = "Resumen"
        ws["A1"] = f"Reporte de gastos — {MESES[month - 1].capitalize()} {year}"
        ws["A1"].font = Font(bold=True, size=14)
        dias = len(s["por_dia"])
        filas = [("Total gastado", s["total"]), ("Número de gastos", s["n"]),
                 ("Promedio por gasto", s["total"] / s["n"]),
                 ("Promedio por día con gastos", s["total"] / dias),
                 ("Mayor gasto", f"{money(s['mayor'].monto)} — {s['mayor'].descripcion}")]
        for i, (k, v) in enumerate(filas, start=3):
            ws.cell(i, 1, k).font = bold
            c = ws.cell(i, 2, v)
            if isinstance(v, float):
                c.number_format = excel_format()

        start = 10
        for j, h in enumerate(["Categoría", "Monto", "% del total"], start=1):
            c = ws.cell(start, j, h)
            c.font, c.fill = head_font, head_fill
        for i, (cat, monto) in enumerate(s["por_categoria"].items(), start=start + 1):
            ws.cell(i, 1, cat)
            ws.cell(i, 2, monto).number_format = excel_format()
            ws.cell(i, 3, monto / s["total"]).number_format = "0.0%"
        end = start + len(s["por_categoria"])
        ws.column_dimensions["A"].width = 30
        ws.column_dimensions["B"].width = 40
        ws.column_dimensions["C"].width = 12

        pie = PieChart()
        pie.title = "Gastos por categoría"
        pie.add_data(Reference(ws, min_col=2, min_row=start, max_row=end), titles_from_data=True)
        pie.set_categories(Reference(ws, min_col=1, min_row=start + 1, max_row=end))
        ws.add_chart(pie, "E3")

        wd = wb.create_sheet("Por día")
        wd.append(["Fecha", "Monto"])
        for c in wd[1]:
            c.font, c.fill = head_font, head_fill
        for d, m in s["por_dia"].items():
            wd.append([d, m])
            wd.cell(wd.max_row, 1).number_format = "DD/MM/YYYY"
            wd.cell(wd.max_row, 2).number_format = excel_format()
        wd.column_dimensions["A"].width = 12
        bar = BarChart()
        bar.title = "Gasto diario"
        bar.add_data(Reference(wd, min_col=2, min_row=1, max_row=wd.max_row), titles_from_data=True)
        bar.set_categories(Reference(wd, min_col=1, min_row=2, max_row=wd.max_row))
        bar.width = 24
        wd.add_chart(bar, "D2")

        det = wb.create_sheet("Detalle")
        det.append(HEADERS)
        for c in det[1]:
            c.font, c.fill = head_font, head_fill
        for e in sorted(items, key=lambda e: (e.fecha, e.hora)):
            det.append([e.fecha, e.hora, e.monto, e.categoria, e.descripcion])
            det.cell(det.max_row, 1).number_format = "DD/MM/YYYY"
            det.cell(det.max_row, 3).number_format = excel_format()
        for col, width in zip("ABCDE", (12, 8, 12, 14, 40)):
            det.column_dimensions[col].width = width

        self.reports_dir.mkdir(parents=True, exist_ok=True)
        path = self.report_path(year, month)
        wb.save(path)
        return path, s


def summary_text(s: dict, year: int, month: int, top: int = 5) -> str:
    nombre = f"{MESES[month - 1]} {year}"
    if not s["n"]:
        return f"No tengo gastos registrados en {nombre}."
    lineas = [f"En {nombre} llevas {money(s['total'])} en {s['n']} gastos."]
    for cat, monto in list(s["por_categoria"].items())[:top]:
        lineas.append(f"  • {cat}: {money(monto)} ({monto / s['total']:.0%})")
    return "\n".join(lineas)
