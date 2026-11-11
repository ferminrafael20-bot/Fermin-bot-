"""Pruebas de agenda, recordatorios, archivos, tienda, PC, notas y tareas."""

import json
from datetime import datetime

import pytest

from alfred import Alfred
from alfred.agenda import Agenda
from alfred.dateparse import parse_when
from alfred.tareas import Scheduler

NOW = datetime(2026, 11, 11, 15, 0)  # miércoles


class Clock:
    def __init__(self, dt):
        self.dt = dt

    def __call__(self):
        return self.dt


@pytest.fixture
def alfred(tmp_path, monkeypatch):
    for var in ("ALFRED_EMAIL_USER", "ALFRED_TELEGRAM_TOKEN", "ALFRED_SHOPIFY_STORE"):
        monkeypatch.delenv(var, raising=False)
    clock = Clock(NOW)
    a = Alfred(data_dir=tmp_path / "datos", clock=clock, brain=False)
    a.clock = clock
    a.avisos = []
    a.ctx.extras["notifier"] = lambda asunto, cuerpo: a.avisos.append((asunto, cuerpo))
    return a


@pytest.mark.parametrize("texto,esperado,semanal", [
    ("manana a las 9 pagar", datetime(2026, 11, 12, 9, 0), False),
    ("en 20 minutos", datetime(2026, 11, 11, 15, 20), False),
    ("el martes a las 6 de la tarde", datetime(2026, 11, 17, 18, 0), False),
    ("todos los jueves a las 19", datetime(2026, 11, 12, 19, 0), True),
    ("el 20 de diciembre a las 10", datetime(2026, 12, 20, 10, 0), False),
    ("15/12 a las 18:30", datetime(2026, 12, 15, 18, 30), False),
    ("a las 10", datetime(2026, 11, 12, 10, 0), False),  # ya pasó hoy -> mañana
    ("el miercoles a las 9", datetime(2026, 11, 18, 9, 0), False),
])
def test_parse_when(texto, esperado, semanal):
    when, _, sem = parse_when(texto, NOW)
    assert when == esperado and sem == semanal


def test_parse_when_none():
    assert parse_when("comprar pan", NOW)[0] is None


def test_reminder_is_sent_on_time(alfred):
    assert "pagar la luz de Mamá" in alfred.handle("Recuérdame en 20 minutos pagar la luz de Mamá")
    sched = Scheduler(alfred)
    sched.recordatorios()
    assert alfred.avisos == []
    alfred.clock.dt = datetime(2026, 11, 11, 15, 21)
    sched.recordatorios()
    assert alfred.avisos and "pagar la luz de Mamá" in alfred.avisos[0][0]
    sched.recordatorios()
    assert len(alfred.avisos) == 1  # no se repite


def test_class_reminder_day_before(alfred, monkeypatch):
    monkeypatch.setenv("ALFRED_HORA_AVISO", "10:00")
    alfred.handle("todos los jueves clase con Sofía Pérez a las 7 de la tarde")
    alfred.handle("agenda el torneo Copa Primavera el 13 de noviembre a las 10")
    sched = Scheduler(alfred)
    sched.aviso_dia_antes()  # miércoles 15:00 -> mañana jueves hay clase
    asunto, cuerpo = alfred.avisos[0]
    assert "Sofía Pérez" in cuerpo and "escríbele" in cuerpo
    sched.aviso_dia_antes()
    assert len(alfred.avisos) == 1  # una vez al día
    alfred.clock.dt = datetime(2026, 11, 12, 9, 0)
    sched.aviso_dia_antes()  # antes de las 10: aún no
    assert len(alfred.avisos) == 1
    alfred.clock.dt = datetime(2026, 11, 12, 10, 5)
    sched.aviso_dia_antes()
    assert "Copa Primavera" in alfred.avisos[1][1]


def test_agenda_queries_and_export(alfred):
    alfred.handle("tengo clase con Juan el martes a las 18")
    alfred.handle("agenda el torneo Copa Primavera el 20 de diciembre a las 10")
    assert "Juan" in alfred.handle("¿qué clases tengo el martes?")
    assert "No tienes nada" in alfred.handle("¿qué clases tengo mañana?")
    assert "Copa Primavera" in alfred.handle("mis próximos torneos")
    out = alfred.handle("exporta mi calendario")
    ics = (alfred.ctx.data_dir / "calendario_alfred.ics").read_text()
    assert "SUMMARY:Torneo Copa Primavera" in ics and "BEGIN:VEVENT" in ics and ".ics" in out
    assert "Borrado" in alfred.handle("borra el evento 1")
    assert len(Agenda(alfred.ctx.data_dir).all()) == 1


def test_organize_files_with_confirmation_and_undo(alfred, tmp_path):
    carpeta = tmp_path / "Descargas"
    carpeta.mkdir()
    for nombre in ("foto.jpg", "foto2.PNG", "factura.pdf", "datos.xlsx", "raro.xyz"):
        (carpeta / nombre).write_text("x")
    (carpeta / "foto.jpg.bak").write_text("x")
    out = alfred.handle(f"organiza la carpeta {carpeta}")
    assert "6 archivos" in out and "sí" in out
    assert (carpeta / "factura.pdf").exists()  # aún no se movió nada
    assert "moví 6" in alfred.handle("sí")
    assert (carpeta / "Imágenes" / "foto2.PNG").exists()
    assert (carpeta / "Documentos" / "factura.pdf").exists()
    assert (carpeta / "Otros" / "raro.xyz").exists()
    assert "Devolví 6" in alfred.handle("deshaz la organización")
    assert (carpeta / "factura.pdf").exists() and not (carpeta / "Documentos").exists()


def test_cancel_pending_action(alfred, tmp_path):
    carpeta = tmp_path / "x"
    carpeta.mkdir()
    (carpeta / "a.pdf").write_text("x")
    alfred.handle(f"organiza la carpeta {carpeta}")
    assert "Cancelado" in alfred.handle("no")
    assert (carpeta / "a.pdf").exists()
    assert "No entendí" in alfred.handle("sí")  # ya no hay nada pendiente


def test_open_sites(alfred, monkeypatch):
    abiertos = []
    monkeypatch.setattr("webbrowser.open", abiertos.append)
    assert "Abrí youtube" in alfred.handle("abre youtube")
    assert "EasyCancha" in alfred.handle("reserva una cancha para el sábado")
    assert abiertos == ["https://www.youtube.com", "https://www.easycancha.com"]


def test_notes(alfred):
    alfred.handle("guarda la idea Video: 5 IAs gratis para crear contenido")
    alfred.handle("nota: llamar al proveedor")
    assert "5 IAs gratis" in alfred.handle("mis ideas")
    assert "proveedor" not in alfred.handle("mis ideas")
    assert "proveedor" in alfred.handle("mis notas")


PRODUCTOS = [
    {"id": "gid://shopify/Product/1", "title": "Sérum Vitamina C", "handle": "serum", "status": "ACTIVE",
     "totalInventory": 0, "descriptionHtml": "<p>Bueno</p>", "tags": [], "featuredMedia": None,
     "seo": {"title": None, "description": None},
     "variants": {"nodes": [{"id": "v1", "price": "10.00", "compareAtPrice": "9.00", "sku": ""}]}},
    {"id": "gid://shopify/Product/2", "title": "Labial", "handle": "labial", "status": "ACTIVE",
     "totalInventory": 5, "descriptionHtml": "<p>" + "Muy buen labial de larga duración. " * 4 + "</p>",
     "tags": ["labios"], "featuredMedia": {"id": "m"},
     "seo": {"title": "Labial", "description": "Labial de larga duración"},
     "variants": {"nodes": [{"id": "v2", "price": "8.00", "compareAtPrice": None, "sku": "LAB-1"}]}},
]


def test_shopify_audit(tmp_path):
    from alfred import shopify
    resumen, path = shopify.audit(tmp_path, products=PRODUCTOS)
    assert "Revisé 2 productos: 1 tienen algo por mejorar" in resumen
    assert "Sin imagen" in resumen and path.exists()
    assert shopify.issues(PRODUCTOS[1]) == []


def test_shopify_update_requires_confirmation(alfred, monkeypatch):
    from alfred import shopify
    from alfred.core import registered_tools
    monkeypatch.setenv("ALFRED_SHOPIFY_STORE", "mitienda")
    monkeypatch.setenv("ALFRED_SHOPIFY_TOKEN", "shpat_x")
    llamadas = []
    monkeypatch.setattr(shopify, "graphql", lambda q, v=None: llamadas.append(v) or
                        {"productUpdate": {"product": {}, "userErrors": []}})
    t = next(t for t in registered_tools() if t.name == "actualizar_producto_shopify")
    out = t.fn(alfred.ctx, {"producto_id": "gid://shopify/Product/1", "titulo": "", "descripcion_html": "",
                            "seo_titulo": "", "seo_descripcion": "Sérum con vitamina C", "etiquetas": "piel, sérum",
                            "estado": "", "precio": "", "variantes_ids": []})
    assert "sí" in out and llamadas == []
    assert "Actualicé" in alfred.handle("sí")
    assert llamadas[0]["product"]["seo"] == {"description": "Sérum con vitamina C"}
    assert llamadas[0]["product"]["tags"] == ["piel", "sérum"]


def test_shopify_not_configured(alfred):
    assert "no está conectada" in alfred.handle("audita mi tienda")


def test_news_needs_claude(alfred):
    assert "necesito Claude" in alfred.handle("noticias del día")


def test_news_scheduled_once(alfred, monkeypatch):
    monkeypatch.setenv("ALFRED_EMAIL_USER", "a@b.c")
    monkeypatch.setenv("ALFRED_EMAIL_PASSWORD", "x")
    enviados = []
    monkeypatch.setattr("alfred.news.build_digest", lambda brain, now: "noticias")
    monkeypatch.setattr("alfred.notify.send_email", lambda a, c, to=None: enviados.append(a))
    alfred.ctx.extras["brain"] = object()
    sched = Scheduler(alfred)
    alfred.clock.dt = datetime(2026, 11, 12, 5, 59)
    sched.noticias()
    assert enviados == []
    alfred.clock.dt = datetime(2026, 11, 12, 6, 0)
    sched.noticias()
    sched.noticias()
    assert len(enviados) == 1


def test_telegram_only_answers_owner(alfred, monkeypatch):
    from alfred import telegram
    monkeypatch.setenv("ALFRED_TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ALFRED_TELEGRAM_CHAT_ID", "111")
    enviados = []

    def fake_call(method, http_timeout=30, **params):
        if method == "getUpdates":
            return [{"update_id": 1, "message": {"text": "gasté 10 en pan", "chat": {"id": 111}}},
                    {"update_id": 2, "message": {"text": "borra el último gasto", "chat": {"id": 999}}}]
        enviados.append((params["chat_id"], params["text"]))

    monkeypatch.setattr(telegram, "_call", fake_call)
    bridge = telegram.TelegramBridge(alfred)
    bridge.poll()
    assert enviados[0][0] == "111" and "Anotado" in enviados[0][1]
    assert enviados[1] == ("999", "No estoy autorizado para hablar contigo.")
    assert bridge.offset == 3


def test_env_file_loading(tmp_path, monkeypatch):
    monkeypatch.delenv("ALFRED_PRUEBA", raising=False)
    datos = tmp_path / "d"
    datos.mkdir()
    (datos / ".env").write_text('# comentario\nALFRED_PRUEBA="hola"\n')
    Alfred(data_dir=datos, brain=False)
    import os
    assert os.environ["ALFRED_PRUEBA"] == "hola"
    monkeypatch.delenv("ALFRED_PRUEBA")


def test_profile_template_created(alfred):
    from alfred import profile
    assert profile.load(alfred.ctx.data_dir) == ""  # plantilla vacía
    assert "Perfil de inversor" in (alfred.ctx.data_dir / "perfil.md").read_text()


def test_pesos_chilenos_clp(alfred, monkeypatch):
    monkeypatch.setenv("ALFRED_MONEDA", "CLP")
    assert alfred.handle("gasté 15.990 en el Jumbo") == "Anotado: $15.990 en Comida (Jumbo)."
    assert "$5.000 en Transporte" in alfred.handle("gasté 5 lucas en bencina")
    assert "$1.000" in alfred.handle("gasté una luca en pan")
    assert "$2.000.000 en Hogar" in alfred.handle("pagué 2 palos de arriendo")
    assert "$2.021.990" in alfred.handle("¿cuánto llevo gastado este mes?")
    from openpyxl import load_workbook
    ws = load_workbook(alfred.ctx.data_dir / "gastos.xlsx")["Gastos"]
    assert ws["C2"].number_format == '"$"#,##0'


def test_voz_espanol_prefiere_chile():
    from alfred.voice import _voz_espanol

    class V:
        def __init__(self, id, name, languages):
            self.id, self.name, self.languages = id, name, languages

    voces = [V("en", "Samantha", ["en_US"]), V("es", "Mónica", ["es_ES"]),
             V("mx", "Paulina", ["es_MX"]), V("cl", "Francisca", ["es-CL"])]
    assert _voz_espanol(voces) == "cl"
    assert _voz_espanol(voces[:3]) == "mx"
    assert _voz_espanol([V("w", "Microsoft Sabina Desktop - Spanish (Mexico)", [])]) == "w"
    assert _voz_espanol(voces[:1]) is None
