"""Agenda de Alfred: clases, torneos, eventos y recordatorios.

Se guarda en ``<data_dir>/agenda.json`` y se puede exportar a un archivo
.ics para importarlo en Google Calendar, Outlook o el calendario del celular.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

TIPOS = ("clase", "torneo", "evento", "recordatorio")
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


@dataclass
class Event:
    id: int
    tipo: str
    titulo: str
    fecha: str              # ISO "2026-11-20T18:00"
    persona: str = ""
    lugar: str = ""
    semanal: bool = False
    enviado: bool = False   # recordatorios ya avisados

    @property
    def dt(self) -> datetime:
        return datetime.fromisoformat(self.fecha)

    def describe(self, when: datetime | None = None) -> str:
        when = when or self.dt
        txt = f"{self.titulo}" if self.tipo != "clase" else f"Clase con {self.persona or self.titulo}"
        if self.tipo == "torneo" and not txt.lower().startswith("torneo"):
            txt = f"Torneo {txt}"
        extra = f" en {self.lugar}" if self.lugar else ""
        rep = f" (todos los {DIAS[self.dt.weekday()]})" if self.semanal else ""
        return f"#{self.id} {txt}{extra}: {fecha_humana(when)}{rep}"


def fecha_humana(d: datetime) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} a las {d:%H:%M}"


class Agenda:
    def __init__(self, data_dir: Path):
        self.path = Path(data_dir) / "agenda.json"

    def _load(self) -> list[Event]:
        if not self.path.exists():
            return []
        return [Event(**e) for e in json.loads(self.path.read_text(encoding="utf-8"))]

    def _save(self, events: list[Event]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([asdict(e) for e in events], ensure_ascii=False, indent=1),
                             encoding="utf-8")

    def all(self) -> list[Event]:
        return self._load()

    def add(self, tipo: str, titulo: str, when: datetime, persona: str = "", lugar: str = "",
            semanal: bool = False) -> Event:
        if tipo not in TIPOS:
            raise ValueError(f"tipo inválido: {tipo}")
        events = self._load()
        ev = Event(max((e.id for e in events), default=0) + 1, tipo, titulo.strip(),
                   when.strftime("%Y-%m-%dT%H:%M"), persona.strip(), lugar.strip(), semanal)
        events.append(ev)
        self._save(events)
        return ev

    def remove(self, event_id: int) -> Event | None:
        events = self._load()
        for e in events:
            if e.id == event_id:
                self._save([x for x in events if x.id != event_id])
                return e
        return None

    def occurrences(self, start: datetime, end: datetime, tipos=None) -> list[tuple[datetime, Event]]:
        out = []
        for e in self._load():
            if tipos and e.tipo not in tipos:
                continue
            if e.semanal:
                d = e.dt
                if d < start:
                    d += timedelta(weeks=-(-(start - d) // timedelta(weeks=1)))
                while d < end:
                    out.append((d, e))
                    d += timedelta(weeks=1)
            elif start <= e.dt < end:
                out.append((e.dt, e))
        return sorted(out, key=lambda x: x[0])

    def due_reminders(self, now: datetime) -> list[Event]:
        return [e for e in self._load() if e.tipo == "recordatorio" and not e.enviado and e.dt <= now]

    def mark_sent(self, ids: list[int]) -> None:
        events = self._load()
        for e in events:
            if e.id in ids:
                e.enviado = True
        self._save(events)

    def on_day(self, day: date, tipos=("clase", "torneo", "evento")):
        start = datetime(day.year, day.month, day.day)
        return self.occurrences(start, start + timedelta(days=1), tipos)

    def export_ics(self, path: Path) -> Path:
        def esc(s):
            return s.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Alfred//ES"]
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        for e in self._load():
            if e.tipo == "recordatorio":
                continue
            ini = e.dt
            lines += ["BEGIN:VEVENT", f"UID:alfred-{e.id}@alfred", f"DTSTAMP:{stamp}",
                      f"DTSTART:{ini:%Y%m%dT%H%M%S}",
                      f"DTEND:{ini + timedelta(hours=1):%Y%m%dT%H%M%S}",
                      f"SUMMARY:{esc(e.describe().split(': ')[0].split(' ', 1)[1])}"]
            if e.lugar:
                lines.append(f"LOCATION:{esc(e.lugar)}")
            if e.semanal:
                lines.append("RRULE:FREQ=WEEKLY")
            lines += ["BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY",
                      "DESCRIPTION:Recordatorio", "END:VALARM", "END:VEVENT"]
        lines.append("END:VCALENDAR")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
        return path
