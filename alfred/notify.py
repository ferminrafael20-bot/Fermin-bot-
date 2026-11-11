"""Avisos de Alfred: pantalla, correo electrónico y Telegram.

Correo (Gmail): crea una "contraseña de aplicación" en tu cuenta de Google
(Seguridad -> Verificación en 2 pasos -> Contraseñas de aplicaciones) y pon:
  ALFRED_EMAIL_USER=tucorreo@gmail.com
  ALFRED_EMAIL_PASSWORD=la-contraseña-de-aplicación
  ALFRED_EMAIL_TO=destino@gmail.com      (opcional, por defecto el mismo)
  ALFRED_SMTP_HOST / ALFRED_SMTP_PORT    (opcional, por defecto Gmail)
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage


def email_configured() -> bool:
    return bool(os.environ.get("ALFRED_EMAIL_USER") and os.environ.get("ALFRED_EMAIL_PASSWORD"))


def send_email(asunto: str, cuerpo: str, to: str | None = None) -> None:
    user = os.environ["ALFRED_EMAIL_USER"]
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = user
    msg["To"] = to or os.environ.get("ALFRED_EMAIL_TO") or user
    msg.set_content(cuerpo)
    host = os.environ.get("ALFRED_SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("ALFRED_SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=30) as smtp:
        smtp.login(user, os.environ["ALFRED_EMAIL_PASSWORD"])
        smtp.send_message(msg)


def notify(ctx, asunto: str, cuerpo: str, email: bool = True) -> list[str]:
    """Envía un aviso por todos los canales configurados. Devuelve los usados."""
    custom = ctx.extras.get("notifier")
    if custom:  # para pruebas o canales propios
        custom(asunto, cuerpo)
        return ["personalizado"]

    canales, errores = [], []
    printer = ctx.extras.get("printer")
    if printer:
        printer(f"🔔 {asunto}\n{cuerpo}")
        canales.append("pantalla")
    if email and email_configured():
        try:
            send_email(asunto, cuerpo)
            canales.append("correo")
        except Exception as exc:
            errores.append(f"correo: {exc}")
    from . import telegram
    if telegram.configured():
        try:
            telegram.send(f"🔔 {asunto}\n\n{cuerpo}")
            canales.append("telegram")
        except Exception as exc:
            errores.append(f"telegram: {exc}")
    if errores and printer:
        printer("No pude enviar el aviso por " + "; ".join(errores))
    return canales
