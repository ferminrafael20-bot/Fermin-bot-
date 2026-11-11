"""Noticias de cripto, forex y acciones.

"noticias del día" -> te las muestra; "mándame las noticias" -> te las envía por correo.
Cada día a las 6:00 (ALFRED_HORA_NOTICIAS) se envían solas si Alfred está en modo servicio.
"""

from alfred import news, notify
from alfred.core import command


def _brain(ctx):
    brain = ctx.extras.get("brain")
    if not brain:
        raise RuntimeError("Para las noticias necesito Claude (configura ANTHROPIC_API_KEY).")
    return brain


def enviar_noticias(ctx) -> str:
    texto = news.build_digest(_brain(ctx), ctx.now())
    if not notify.email_configured():
        return texto + "\n\n(No te lo envié por correo: falta configurar ALFRED_EMAIL_USER y ALFRED_EMAIL_PASSWORD.)"
    notify.send_email(f"Alfred · Noticias de mercados {ctx.now():%d/%m/%Y}", texto)
    return "Te envié las noticias de hoy a tu correo."


@command("noticias", [r"\b(?:manda|envia|enviar|mandar)(?:me)?\b.*\bnoticias\b", r"\bnoticias\b"],
         help="Resumen de noticias de cripto, forex y acciones (o por correo con 'mándame').",
         examples=["noticias del día", "mándame las noticias por correo"], priority=35)
def noticias(ctx, match, texto):
    if match.re.pattern.startswith(r"\b(?:manda"):
        return enviar_noticias(ctx)
    return news.build_digest(_brain(ctx), ctx.now())
