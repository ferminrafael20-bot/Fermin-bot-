"""Tareas automáticas de Alfred.

* Recordatorios: avisa cuando llega la hora.
* Un día antes: avisa de las clases, torneos y eventos de mañana
  (a la hora ALFRED_HORA_AVISO, por defecto 10:00), con quién es cada clase
  para que le escribas.
* Noticias: envía por correo el resumen de mercados a ALFRED_HORA_NOTICIAS
  (por defecto 06:00). Si el PC estaba apagado, lo envía al encenderse,
  siempre que sea antes de las 12:00.

Se ejecutan mientras Alfred está abierto o en modo ``--servicio``.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, time, timedelta

from .agenda import Agenda
from .notify import notify


def _hora(var: str, defecto: str) -> time:
    h, m = os.environ.get(var, defecto).split(":")
    return time(int(h), int(m))


class Scheduler:
    def __init__(self, alfred):
        self.alfred = alfred
        self.ctx = alfred.ctx
        self.state_path = self.ctx.data_dir / "estado.json"

    def _state(self) -> dict:
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _mark(self, key: str, value: str) -> None:
        st = self._state()
        st[key] = value
        self.state_path.write_text(json.dumps(st), encoding="utf-8")

    def check(self) -> list[str]:
        """Revisa y ejecuta lo que toque ahora. Devuelve lo que hizo."""
        hechos = []
        with self.alfred.lock:
            for tarea in (self.recordatorios, self.aviso_dia_antes, self.noticias):
                try:
                    r = tarea()
                except Exception as exc:
                    r = f"Error en {tarea.__name__}: {exc}"
                    printer = self.ctx.extras.get("printer")
                    if printer:
                        printer(r)
                if r:
                    hechos.append(r)
        return hechos

    def recordatorios(self):
        agenda = Agenda(self.ctx.data_dir)
        vencidos = agenda.due_reminders(self.ctx.now())
        for ev in vencidos:
            notify(self.ctx, f"Recordatorio: {ev.titulo}", f"Te recuerdo: {ev.titulo}.\n\n— Alfred")
        agenda.mark_sent([e.id for e in vencidos])
        return f"{len(vencidos)} recordatorios enviados" if vencidos else None

    def aviso_dia_antes(self):
        now = self.ctx.now()
        hoy = now.date().isoformat()
        if now.time() < _hora("ALFRED_HORA_AVISO", "10:00") or self._state().get("aviso_dia_antes") == hoy:
            return None
        self._mark("aviso_dia_antes", hoy)
        manana = Agenda(self.ctx.data_dir).on_day(now.date() + timedelta(days=1))
        if not manana:
            return None
        lineas = []
        for d, e in manana:
            if e.tipo == "clase":
                lineas.append(f"• {d:%H:%M} clase con {e.persona or e.titulo}: escríbele para confirmar.")
            elif e.tipo == "torneo":
                lineas.append(f"• {d:%H:%M} torneo {e.titulo}" + (f" en {e.lugar}" if e.lugar else "")
                              + ": revisa inscripción, horario y equipo.")
            else:
                lineas.append(f"• {d:%H:%M} {e.titulo}" + (f" en {e.lugar}" if e.lugar else ""))
        notify(self.ctx, "Lo que tienes mañana", "Mañana tienes:\n" + "\n".join(lineas) + "\n\n— Alfred")
        return f"aviso de mañana ({len(manana)} eventos)"

    def noticias(self):
        now = self.ctx.now()
        hoy = now.date().isoformat()
        inicio = _hora("ALFRED_HORA_NOTICIAS", "06:00")
        limite = (datetime.combine(now.date(), inicio) + timedelta(hours=6)).time()
        if not (inicio <= now.time() < limite) or self._state().get("noticias") == hoy:
            return None
        if not self.ctx.extras.get("brain"):
            return None
        from .notify import email_configured
        if not email_configured():
            return None
        self._mark("noticias", hoy)
        from .commands.noticias import enviar_noticias
        return enviar_noticias(self.ctx)
