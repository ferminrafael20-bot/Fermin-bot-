from datetime import datetime

import pytest
from openpyxl import load_workbook

from alfred import Alfred, command
from alfred.core import normalize
from alfred.expenses import ExpenseBook, categorize, parse_expense, parse_number


class Clock:
    def __init__(self, dt):
        self.dt = dt

    def __call__(self):
        return self.dt


@pytest.fixture
def alfred(tmp_path):
    clock = Clock(datetime(2026, 10, 15, 10, 30))
    j = Alfred(data_dir=tmp_path, clock=clock, brain=False)
    j.clock = clock
    return j


@pytest.mark.parametrize("raw,expected", [
    ("25", 25), ("25.50", 25.5), ("25,5", 25.5), ("1.200", 1200),
    ("1,200", 1200), ("1.200,50", 1200.5), ("1,200.50", 1200.5), ("1.000.000", 1_000_000),
])
def test_parse_number(raw, expected):
    assert parse_number(raw) == pytest.approx(expected)


def test_parse_expense_and_category():
    assert parse_expense("25.50 en el super") == (25.5, "super")
    assert parse_expense("2 mil en ropa") == (2000, "ropa")
    assert parse_expense("$300 pesos de uber") == (300, "uber")
    assert parse_expense("nada") is None
    assert categorize("super") == "Comida"
    assert categorize("gasolina del carro") == "Transporte"
    assert categorize("algo raro") == "Otros"


def test_normalize():
    assert normalize("Oye Alfred, ¿Cuánto llevo gastado?") == "cuanto llevo gastado"
    assert normalize("Alfredo qué hora es") == "que hora es"


def test_register_and_summary(alfred, tmp_path):
    assert "Comida" in alfred.handle("gasté 25.50 en el súper")
    assert "Hogar" in alfred.handle("Alfred, pagué 1.200 de renta")
    assert "Ocio" in alfred.handle("compré 40 de regalo categoría ocio")
    resumen = alfred.handle("¿cuánto llevo gastado este mes?")
    assert "$1,265.50" in resumen and "3 gastos" in resumen

    ws = load_workbook(tmp_path / "gastos.xlsx")["Gastos"]
    assert ws.max_row == 4
    assert ws["C2"].value == 25.5 and ws["D3"].value == "Hogar"

    assert "regalo" in alfred.handle("borra el último gasto")
    assert "2 gastos" in alfred.handle("resumen de gastos")


def test_monthly_report(alfred, tmp_path):
    alfred.handle("gasté 100 en gasolina")
    alfred.handle("gasté 50 en farmacia")
    out = alfred.handle("reporte del mes")
    path = tmp_path / "reportes" / "reporte_2026-10.xlsx"
    assert str(path) in out and path.exists()
    wb = load_workbook(path)
    assert wb.sheetnames == ["Resumen", "Por día", "Detalle"]
    assert wb["Resumen"]["B3"].value == 150
    assert "No hay gastos" in alfred.handle("reporte de marzo")


def test_auto_report_on_new_month(alfred, tmp_path):
    alfred.handle("gasté 100 en cine")
    assert alfred.startup() == []  # el mes aún no termina
    alfred.clock.dt = datetime(2026, 11, 1, 9, 0)
    msgs = alfred.startup()
    assert len(msgs) == 1 and "octubre" in msgs[0]
    assert (tmp_path / "reportes" / "reporte_2026-10.xlsx").exists()
    assert alfred.startup() == []  # no lo repite
    assert "$100.00" in alfred.handle("cuanto gaste el mes pasado")


def test_trading_signal_offline(alfred):
    out = alfred.handle("señal de btc con datos de prueba")
    assert out.startswith("BTC/USDT") and "datos de prueba" in out


def test_new_command_plugin(alfred):
    @command("eco", r"^repite (.+)$", help="Repite lo que dices.")
    def eco(ctx, match, texto):
        return match.group(1)

    assert alfred.handle("repite hola mundo") == "hola mundo"
    assert "eco" in alfred.handle("ayuda")


def test_unknown_and_exit(alfred):
    assert "No entendí" in alfred.handle("baila salsa")
    alfred.handle("adiós")
    assert alfred.should_exit


def test_book_month_filter(tmp_path):
    book = ExpenseBook(tmp_path)
    book.add(10, "cafe", when=datetime(2026, 9, 30))
    book.add(20, "cafe", when=datetime(2026, 10, 1))
    assert [e.monto for e in book.month(2026, 10)] == [20]
