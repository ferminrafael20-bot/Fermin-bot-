"""Arranca Alfred.

    python -m alfred                       # modo texto (escribes los comandos)
    python -m alfred --voz                 # modo voz (requiere micrófono)
    python -m alfred -c "gasté 20 en café" # ejecuta un solo comando y sale
    python -m alfred --servicio            # en segundo plano: avisos, noticias y Telegram
    python -m alfred --tarea noticias      # ejecuta una tarea una vez (noticias|avisos)
    python -m alfred --telegram-id         # muestra tu número de chat de Telegram
    python -m alfred --sin-claude          # solo comandos fijos, sin Claude

Si hay credenciales de Anthropic (ANTHROPIC_API_KEY), lo que no entienda un
comando fijo lo responde Claude, que además puede usar las funciones de Alfred.
"""

import argparse
import sys
import threading
import time

from alfred.core import Alfred


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Alfred, tu asistente personal")
    parser.add_argument("-c", "--comando", help="ejecuta un comando y termina")
    parser.add_argument("--voz", action="store_true", help="usar micrófono y altavoz")
    parser.add_argument("--datos", help="carpeta de datos (por defecto ./datos_alfred)")
    parser.add_argument("--sin-claude", action="store_true", help="usar solo los comandos fijos")
    parser.add_argument("--servicio", action="store_true",
                        help="modo servicio: recordatorios, noticias y Telegram, sin teclado")
    parser.add_argument("--tarea", choices=["noticias", "avisos"], help="ejecuta una tarea y termina")
    parser.add_argument("--telegram-id", action="store_true", help="muestra tus chats de Telegram")
    args = parser.parse_args(argv)

    if args.telegram_id:
        from alfred import telegram
        from alfred.core import load_env
        from pathlib import Path
        load_env(Path.cwd() / ".env")
        chats = telegram.discover_chats()
        print("\n".join(chats) if chats else "Escríbele algo a tu bot y vuelve a ejecutar esto.")
        return 0

    alfred = Alfred(data_dir=args.datos, brain=False if args.sin_claude else None)
    from alfred.tareas import Scheduler
    scheduler = Scheduler(alfred)

    if args.comando:
        print(alfred.handle(args.comando))
        return 0
    if args.tarea == "noticias":
        from alfred.commands.noticias import enviar_noticias
        print(enviar_noticias(alfred.ctx))
        return 0

    alfred.ctx.extras["printer"] = lambda t: print(f"\nAlfred: {t}")
    if args.tarea == "avisos":
        print(scheduler.check() or "Nada pendiente.")
        return 0
    if args.servicio:
        return servicio(alfred, scheduler)

    voice = None
    if args.voz:
        from alfred.voice import Voice
        voice = Voice()

    def say(text: str) -> None:
        print(f"Alfred: {text}")
        if voice:
            voice.say(text if len(text) < 400 else text.split("\n")[0])

    for msg in alfred.startup():
        say(msg)
    if alfred.brain:
        print(f"(conectado a Claude: {alfred.brain.model})")
    elif not args.sin_claude:
        print("(Claude desactivado: define ANTHROPIC_API_KEY para conectarlo)")
    say("A su servicio. Diga 'ayuda' para ver lo que sé hacer.")

    def revisar():
        while not alfred.should_exit:
            scheduler.check()
            time.sleep(30)

    threading.Thread(target=revisar, daemon=True).start()

    while not alfred.should_exit:
        try:
            if voice:
                print("(escuchando...)")
                texto = voice.listen()
                if not texto:
                    continue
                print(f"Tú: {texto}")
            else:
                texto = input("Tú: ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        say(alfred.handle(texto))
    return 0


def servicio(alfred, scheduler) -> int:
    from alfred import telegram
    puente = telegram.TelegramBridge(alfred) if telegram.configured() else None
    for msg in alfred.startup():
        print(msg)
    print("Alfred en modo servicio" + (" con Telegram" if puente else "") + ". Ctrl+C para salir.")
    try:
        while True:
            scheduler.check()
            if puente:
                try:
                    puente.poll(timeout=25)
                except Exception as exc:
                    print(f"Telegram: {exc}")
                    time.sleep(10)
            else:
                time.sleep(30)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
