"""Arranca Jarvis.

    python -m jarvis                       # modo texto (escribes los comandos)
    python -m jarvis --voz                 # modo voz (requiere micrófono)
    python -m jarvis -c "gasté 20 en café" # ejecuta un solo comando y sale
    python -m jarvis --sin-claude          # solo comandos fijos, sin Claude

Si hay credenciales de Anthropic (ANTHROPIC_API_KEY), lo que no entienda un
comando fijo lo responde Claude, que además puede usar los comandos de Jarvis.

Para el reporte a fin de mes, Jarvis lo genera solo al arrancar si el mes
anterior aún no tiene reporte. También puedes programarlo (cron / Programador
de tareas) el día 1 de cada mes:
    python -m jarvis -c "reporte del mes pasado"
"""

import argparse
import sys

from jarvis.core import Jarvis


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Jarvis, tu asistente personal")
    parser.add_argument("-c", "--comando", help="ejecuta un comando y termina")
    parser.add_argument("--voz", action="store_true", help="usar micrófono y altavoz")
    parser.add_argument("--datos", help="carpeta de datos (por defecto ./datos_jarvis)")
    parser.add_argument("--sin-claude", action="store_true",
                        help="usar solo los comandos fijos, sin Claude")
    args = parser.parse_args(argv)

    jarvis = Jarvis(data_dir=args.datos, brain=False if args.sin_claude else None)

    if args.comando:
        print(jarvis.handle(args.comando))
        return 0

    voice = None
    if args.voz:
        from jarvis.voice import Voice
        voice = Voice()

    def say(text: str) -> None:
        print(f"Jarvis: {text}")
        if voice:
            voice.say(text.split("\n")[0] if len(text) > 300 else text)

    for msg in jarvis.startup():
        say(msg)
    if jarvis.brain:
        print(f"(conectado a Claude: {jarvis.brain.model})")
    elif not args.sin_claude:
        print("(Claude desactivado: define ANTHROPIC_API_KEY para conectarlo)")
    say("A tu servicio. Di 'ayuda' para ver los comandos.")

    while not jarvis.should_exit:
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
        say(jarvis.handle(texto))
    return 0


if __name__ == "__main__":
    sys.exit(main())
