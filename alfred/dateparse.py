"""Interpreta fechas y horas dichas en español (texto ya normalizado).

Ejemplos: "mañana a las 9", "el martes a las 6 de la tarde", "en 20 minutos",
"el 20 de diciembre", "15/12 a las 18:30", "pasado mañana", "todos los lunes".
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

DIAS = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4,
        "sabado": 5, "domingo": 6}
MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
         "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
         "noviembre": 11, "diciembre": 12}
_NUM = {"un": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "diez": 10,
        "quince": 15, "veinte": 20, "treinta": 30}
_DIA_RE = "|".join(DIAS)
_MES_RE = "|".join(MESES)


def _cut(text: str, m: re.Match) -> str:
    return (text[:m.start()] + " " + text[m.end():]).strip()


def parse_when(text: str, now: datetime, default_hour: int = 9):
    """Devuelve ``(fecha_hora | None, texto_sin_la_fecha, semanal)``."""
    rest = text
    semanal = False

    # --- relativas: "en 20 minutos", "dentro de 2 horas", "en media hora"
    m = re.search(r"\b(?:en|dentro de) (\d+|un|una|dos|tres|cuatro|cinco|diez|quince|veinte|treinta|media) "
                  r"(minutos?|horas?|dias?|semanas?)\b", rest)
    if m:
        n = 0.5 if m.group(1) == "media" else float(_NUM.get(m.group(1)) or m.group(1))
        unidad = m.group(2)
        delta = {"m": timedelta(minutes=n), "h": timedelta(hours=n),
                 "d": timedelta(days=n), "s": timedelta(weeks=n)}[unidad[0]]
        return (now + delta).replace(second=0, microsecond=0), _cut(rest, m), False

    # --- hora: "a las 6 de la tarde", "a las 18:30", "a las 7 pm", "al mediodia"
    hora = minuto = None
    m = re.search(r"\b(?:a las?|a eso de las?|tipo|sobre las?) (\d{1,2})(?:[:.h](\d{2}))?\s*"
                  r"(am|pm|a\.m\.|p\.m\.|de la manana|de la tarde|de la noche|hrs|horas|h)?\b", rest)
    if m:
        hora, minuto = int(m.group(1)), int(m.group(2) or 0)
        sufijo = m.group(3) or ""
        if (sufijo.startswith("p") or "tarde" in sufijo or "noche" in sufijo) and hora < 12:
            hora += 12
        if sufijo.startswith("a") or "manana" in sufijo:
            hora = 0 if hora == 12 else hora
        rest = _cut(rest, m)
    else:
        m = re.search(r"\b(al mediodia|a mediodia|a medianoche)\b", rest)
        if m:
            hora, minuto = (0 if "medianoche" in m.group(1) else 12), 0
            rest = _cut(rest, m)
    if hora is not None and not (0 <= hora <= 23 and 0 <= minuto <= 59):
        hora = minuto = None

    # --- fecha
    fecha = None
    patrones = [
        (r"\bpasado manana\b", lambda m: now.date() + timedelta(days=2)),
        (r"\bmanana\b", lambda m: now.date() + timedelta(days=1)),
        (r"\b(?:hoy|esta (?:tarde|noche|manana))\b", lambda m: now.date()),
        (rf"\b(?:todos los|cada) ({_DIA_RE})\b", "semanal"),
        (rf"\b(?:el |este |el proximo |proximo )?({_DIA_RE})(?: que viene)?\b", "dia"),
        (rf"\b(?:el )?(\d{{1,2}}) de ({_MES_RE})(?: (?:de |del )?(\d{{4}}))?\b", "dia_mes"),
        (r"\b(?:el )?(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", "barra"),
        (r"\bel (\d{1,2})\b", "dia_num"),
    ]
    for patron, accion in patrones:
        m = re.search(patron, rest)
        if not m:
            continue
        if callable(accion):
            fecha = accion(m)
        elif accion in ("dia", "semanal"):
            semanal = accion == "semanal"
            dias = (DIAS[m.group(1)] - now.weekday()) % 7
            if dias == 0 and (hora is None or (hora, minuto) <= (now.hour, now.minute)):
                dias = 7
            fecha = now.date() + timedelta(days=dias)
        else:
            try:
                if accion == "dia_mes":
                    d, mes, anio = int(m.group(1)), MESES[m.group(2)], m.group(3)
                elif accion == "barra":
                    d, mes, anio = int(m.group(1)), int(m.group(2)), m.group(3)
                else:
                    d, mes, anio = int(m.group(1)), now.month, None
                y = int(anio) + (2000 if anio and len(anio) == 2 else 0) if anio else now.year
                fecha = datetime(y, mes, d).date()
                if not anio and fecha < now.date():
                    if accion == "dia_num":
                        fecha = (datetime(y + (mes == 12), mes % 12 + 1, d)).date()
                    else:
                        fecha = fecha.replace(year=y + 1)
            except ValueError:
                continue
        rest = _cut(rest, m)
        break

    if fecha is None and hora is None:
        return None, text, False
    if fecha is None:  # solo hora: hoy, o mañana si ya pasó
        fecha = now.date()
        if (hora, minuto) <= (now.hour, now.minute):
            fecha += timedelta(days=1)
    if hora is None:
        hora, minuto = default_hour, 0
    when = datetime(fecha.year, fecha.month, fecha.day, hora, minuto)
    rest = re.sub(r"\s+", " ", rest).strip(" ,.")
    return when, rest, semanal
