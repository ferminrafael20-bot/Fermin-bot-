"""Habla con Alfred desde el celular usando un bot de Telegram.

1. En Telegram, abre @BotFather, envía /newbot y copia el token.
2. Pon ALFRED_TELEGRAM_TOKEN=<token> en tu archivo .env.
3. Escríbele cualquier cosa a tu bot y ejecuta ``python -m alfred --telegram-id``
   para ver tu número de chat. Ponlo en ALFRED_TELEGRAM_CHAT_ID.
4. Deja corriendo ``python -m alfred --servicio`` en tu PC.

Por seguridad, Alfred solo obedece al chat de ALFRED_TELEGRAM_CHAT_ID.
"""

from __future__ import annotations

import json
import os
import urllib.request

LIMITE = 4000  # Telegram admite hasta 4096 caracteres por mensaje


def configured() -> bool:
    return bool(os.environ.get("ALFRED_TELEGRAM_TOKEN") and os.environ.get("ALFRED_TELEGRAM_CHAT_ID"))


def _call(method: str, http_timeout: int = 30, **params):
    token = os.environ["ALFRED_TELEGRAM_TOKEN"]
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(params).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=http_timeout) as resp:
        data = json.loads(resp.read())
    if not data.get("ok"):
        raise RuntimeError(data.get("description", "error de Telegram"))
    return data["result"]


def send(text: str, chat_id: str | None = None) -> None:
    chat_id = chat_id or os.environ["ALFRED_TELEGRAM_CHAT_ID"]
    for i in range(0, len(text), LIMITE):
        _call("sendMessage", chat_id=chat_id, text=text[i:i + LIMITE])


def discover_chats() -> list[str]:
    vistos = {}
    for upd in _call("getUpdates"):
        chat = (upd.get("message") or {}).get("chat")
        if chat:
            vistos[str(chat["id"])] = chat.get("first_name") or chat.get("title") or ""
    return [f"{cid} ({nombre})" for cid, nombre in vistos.items()]


class TelegramBridge:
    """Recibe mensajes del bot y los responde con Alfred."""

    def __init__(self, alfred):
        self.alfred = alfred
        self.offset = None
        self.allowed = os.environ.get("ALFRED_TELEGRAM_CHAT_ID", "")

    def poll(self, timeout: int = 20) -> int:
        params = {"timeout": timeout, "allowed_updates": ["message"]}
        if self.offset is not None:
            params["offset"] = self.offset
        updates = _call("getUpdates", http_timeout=timeout + 10, **params)
        for upd in updates:
            self.offset = upd["update_id"] + 1
            msg = upd.get("message") or {}
            text, chat = msg.get("text"), str((msg.get("chat") or {}).get("id", ""))
            if not text:
                continue
            if chat != self.allowed:
                send("No estoy autorizado para hablar contigo.", chat)
                continue
            if text.strip() == "/start":
                text = "hola"
            send(self.alfred.handle(text), chat)
        return len(updates)
