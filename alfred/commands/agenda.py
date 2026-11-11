"""Recordatorios, clases, torneos y eventos.

Ejemplos:
  "recuérdame mañana a las 9 pagar la luz"
  "recuérdame en 20 minutos sacar la ropa"
  "tengo clase con Juan el martes a las 18"
  "todos los jueves clase con Sofía a las 7 de la tarde"
  "agenda el torneo Copa Primavera el 20 de diciembre a las 10"
  "¿qué clases tengo mañana?" / "mis próximos torneos" / "mis recordatorios"
  "borra el evento 3" / "exporta mi calendario"

Un día antes de cada clase, torneo o evento, Alfred te avisa (ver
ALFRED_HORA_AVISO en tareas.py).
"""

import re
from datetime import datetime, timedelta

from alfred.agenda import TIPOS, Agenda, fecha_humana
from alfred.core import UNKNOWN, command, original_text, tool
from alfred.dateparse import parse_when

PARADAS = {"el", "la", "los", "las", "todos", "cada", "a", "hoy", "manana", "pasado", "en",
           "este", "esta", "proximo", "de", "del", "al", "lunes", "martes", "miercoles",
           "jueves", "viernes", "sabado", "domingo", "y", "para"}


def agenda(ctx) -> Agenda:
    if "agenda" not in ctx.extras:
        ctx.extras["agenda"] = Agenda(ctx.data_dir)
    return ctx.extras["agenda"]


def _sin_fecha(ctx, ejemplo: str) -> str:
    if ctx.extras.get("brain"):
        return UNKNOWN  # que Claude lo interprete o pregunte
    return f"No entendí la fecha. Prueba así: '{ejemplo}'."


# ------------------------------------------------------------ recordatorios --

@command("recordatorio",
         [r"^recuerdame (?:que )?(.+)$", r"^(?:pon|crea|ponme|agrega)(?:me)? (?:un )?recordatorio (?:para |de )?(.+)$",
          r"^avisame (?:que )?(.+)$"],
         help="Crea un recordatorio y te avisa a la hora indicada.",
         examples=["recuérdame mañana a las 9 pagar la luz", "recuérdame en 20 minutos sacar la ropa"],
         priority=15)
def recordatorio(ctx, match, texto):
    when, resto, _ = parse_when(match.group(1), ctx.now())
    if when is None:
        return _sin_fecha(ctx, "recuérdame mañana a las 9 pagar la luz")
    resto = re.sub(r"^(que|de|a|para)\s+", "", resto).strip()
    resto = original_text(texto, resto) if resto else "lo que me pediste"
    if when < ctx.now():
        return f"Esa hora ({when:%H:%M}) ya pasó. Dime otra."
    ev = agenda(ctx).add("recordatorio", resto, when)
    return f"Listo, te recordaré '{ev.titulo}' el {fecha_humana(when)}."


# ---------------------------------------------------------------- clases ----

def _persona(texto: str) -> tuple[str, str]:
    palabras, nombre = texto.split(), []
    while palabras and palabras[0] not in PARADAS and len(nombre) < 3:
        nombre.append(palabras.pop(0))
    return " ".join(nombre).title(), " ".join(palabras)


@command("agendar clase",
         [r"^(?:(?:agenda|agendar|anota|agrega|registra|pon|tengo)(?: una| la)? )?((?:todos los|cada) \w+ )?(?:clases?) con (.+)$"],
         help="Agenda una clase (también semanal) para avisarte un día antes.",
         examples=["tengo clase con Juan el martes a las 18", "todos los jueves clase con Sofía a las 19"],
         priority=16)
def agendar_clase(ctx, match, texto):
    persona, resto = _persona(match.group(2))
    persona = original_text(texto, persona.lower())
    persona = persona if persona[:1].isupper() else persona.title()
    when, _, semanal = parse_when(f"{match.group(1) or ''}{resto}", ctx.now())
    if not persona or when is None:
        return _sin_fecha(ctx, "tengo clase con Juan el martes a las 18")
    ev = agenda(ctx).add("clase", f"Clase con {persona}", when, persona=persona, semanal=semanal)
    rep = " Se repite cada semana." if semanal else ""
    return f"Agendada la clase con {persona} el {fecha_humana(ev.dt)}.{rep} Te aviso un día antes."


# ---------------------------------------------------------------- torneos ---

@command("agendar torneo",
         [r"^(?:agenda|agendar|anota|agrega|registra|tengo|inscribeme en)(?: el| un| una)? torneo (.+)$"],
         help="Agrega un torneo a tu calendario de torneos.",
         examples=["agenda el torneo Copa Primavera el 20 de diciembre a las 10"], priority=16)
def agendar_torneo(ctx, match, texto):
    when, nombre, _ = parse_when(match.group(1), ctx.now())
    if when is None:
        return _sin_fecha(ctx, "agenda el torneo Copa Primavera el 20 de diciembre a las 10")
    nombre = original_text(texto, nombre) if nombre else "sin nombre"
    nombre = nombre if nombre[:1].isupper() else nombre.title()
    ev = agenda(ctx).add("torneo", nombre, when)
    return f"Anotado el torneo {nombre} el {fecha_humana(ev.dt)}. Te aviso un día antes."


# -------------------------------------------------------------- consultar ---

@command("ver agenda",
         [r"\b(clases|torneos|recordatorios|eventos)\b", r"\b(?:mi|la) agenda\b", r"\bcalendario\b",
          r"\bque tengo (hoy|manana|esta semana)\b"],
         help="Muestra tus clases, torneos, eventos o recordatorios próximos.",
         examples=["¿qué clases tengo mañana?", "mis próximos torneos", "mi agenda de la semana"],
         priority=60)
def ver_agenda(ctx, match, texto):
    t = match.string
    tipos = [x for x in TIPOS if re.search(rf"\b{x}(es|s)?\b", t)] or ["clase", "torneo", "evento"]
    hoy = ctx.now().replace(hour=0, minute=0, second=0, microsecond=0)
    dia, _, _ = parse_when(t, ctx.now())
    if "semana" in t:
        ini, fin = ctx.now(), hoy + timedelta(days=8)
    elif dia is not None and "proxim" not in t:
        ini = max(ctx.now(), dia.replace(hour=0, minute=0)) if dia.date() == hoy.date() else dia.replace(hour=0, minute=0)
        fin = dia.replace(hour=0, minute=0) + timedelta(days=1)
    else:
        ini, fin = ctx.now(), hoy + timedelta(days=180 if tipos == ["torneo"] else 30)
    if tipos == ["recordatorio"]:
        items = [(e.dt, e) for e in agenda(ctx).all() if e.tipo == "recordatorio" and not e.enviado]
    else:
        items = agenda(ctx).occurrences(ini, fin, tipos)[:15]
    if not items:
        return "No tienes nada agendado en ese período."
    return "Esto es lo que tienes:\n" + "\n".join(f"  • {e.describe(d)}" for d, e in items)


@command("borrar evento",
         [r"^(?:borra|elimina|cancela|quita)(?:r)? (?:el |la )?(?:evento|recordatorio|clase|torneo) (?:numero |#)?(\d+)$"],
         help="Borra un evento por su número (#).", examples=["borra el evento 3"], priority=10)
def borrar_evento(ctx, match, texto):
    ev = agenda(ctx).remove(int(match.group(1)))
    return f"Borrado: {ev.titulo}." if ev else "No encontré ese número. Di 'mi agenda' para verlos."


@command("exportar calendario", [r"\bexporta(?:r|me)?\b.*\b(calendario|agenda|torneos|clases)\b"],
         help="Crea un archivo .ics para importar en Google Calendar o el celular.",
         examples=["exporta mi calendario"], priority=12)
def exportar(ctx, match, texto):
    path = agenda(ctx).export_ics(ctx.data_dir / "calendario_alfred.ics")
    return (f"Listo: {path}\nImpórtalo en Google Calendar (Configuración → Importar) o ábrelo "
            "en tu celular para agregar todo a tu calendario.")


# ------------------------------------------------------- herramientas Claude --

@tool("crear_evento",
      "Agenda una clase, torneo, evento o recordatorio. Para clases pon el nombre del alumno o "
      "profesor en 'persona'. Los recordatorios avisan a la hora exacta; los demás tipos, un día antes.",
      {"tipo": {"type": "string", "enum": list(TIPOS)},
       "titulo": {"type": "string", "description": "Qué es, p. ej. 'pagar la luz' o 'Copa Primavera'."},
       "fecha_hora": {"type": "string", "description": "Fecha y hora local en formato AAAA-MM-DDTHH:MM."},
       "persona": {"type": "string", "description": "Con quién (solo clases), o vacío."},
       "lugar": {"type": "string", "description": "Dónde, o vacío."},
       "semanal": {"type": "boolean", "description": "true si se repite cada semana."}})
def t_crear_evento(ctx, args):
    when = datetime.fromisoformat(args["fecha_hora"])
    ev = agenda(ctx).add(args["tipo"], args["titulo"], when, args.get("persona", ""),
                         args.get("lugar", ""), bool(args.get("semanal")))
    return f"Agendado: {ev.describe()}"


@tool("consultar_agenda", "Lista los eventos entre dos fechas (AAAA-MM-DD, 'hasta' excluida).",
      {"desde": {"type": "string"}, "hasta": {"type": "string"},
       "tipo": {"type": "string", "enum": list(TIPOS) + ["todos"]}})
def t_consultar_agenda(ctx, args):
    tipos = None if args["tipo"] == "todos" else [args["tipo"]]
    items = agenda(ctx).occurrences(datetime.fromisoformat(args["desde"]),
                                    datetime.fromisoformat(args["hasta"]), tipos)
    return "\n".join(e.describe(d) for d, e in items) or "Nada en ese período."


@tool("borrar_evento", "Borra un evento de la agenda por su número.", {"id": {"type": "integer"}})
def t_borrar_evento(ctx, args):
    ev = agenda(ctx).remove(int(args["id"]))
    return f"Borrado: {ev.titulo}" if ev else "No existe ese número."
