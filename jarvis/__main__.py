"""Arranca Jarvis.

    python -m jarvis                       # modo texto (escribes los comandos)
    python -m jarvis --voz                 # modo voz (requiere micrófono)
    python -m jarvis -c "gasté 20 en café" # ejecuta un solo comando y sale

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
    args = parser.parse_args(argv)

    jarvis = Jarvis(data_dir=args.datos)

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
