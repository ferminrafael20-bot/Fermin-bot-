"""Comandos generales: ayuda, hora, fecha, saludo y salir."""

from alfred.core import UNKNOWN, command, registered_commands

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


@command("ayuda", [r"^(ayuda|help|comandos|que (sabes|puedes) hacer)\b"],
         help="Muestra la lista de comandos.", examples=["ayuda"], priority=0)
def ayuda(ctx, match, texto):
    lineas = ["Esto es lo que sé hacer:"]
    for cmd in registered_commands():
        ejemplo = f"  (ej.: \"{cmd.examples[0]}\")" if cmd.examples else ""
        lineas.append(f"  • {cmd.name}: {cmd.help}{ejemplo}")
    return "\n".join(lineas)


@command("salir", [r"^(salir|adios|chao|apagate|exit|quit)$"],
         help="Cierra Alfred.", examples=["adiós"], priority=0)
def salir(ctx, match, texto):
    ctx.should_exit = True
    return "Hasta luego."


@command("saludo", [r"^(hola|buenos dias|buenas tardes|buenas noches|buenas)\b"],
         help="Te saluda.", examples=["hola alfred"], priority=90)
def saludo(ctx, match, texto):
    hora = ctx.now().hour
    momento = "Buenos días" if hora < 12 else "Buenas tardes" if hora < 20 else "Buenas noches"
    return f"{momento}. ¿En qué te ayudo?"


@command("hora", [r"\bque hora es\b", r"^hora$"], help="Dice la hora.",
         examples=["¿qué hora es?"])
def hora(ctx, match, texto):
    return f"Son las {ctx.now():%H:%M}."


@command("fecha", [r"\bque (dia|fecha) es\b", r"^fecha$"], help="Dice la fecha.",
         examples=["¿qué día es hoy?"])
def fecha(ctx, match, texto):
    d = ctx.now()
    return f"Hoy es {DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}."


@command("nueva conversación", [r"^(nueva conversacion|olvida (todo|la conversacion)|reinicia(r)? (la )?conversacion)$"],
         help="Hace que Claude olvide la conversación actual.",
         examples=["nueva conversación"], priority=5)
def nueva_conversacion(ctx, match, texto):
    brain = ctx.extras.get("brain")
    if brain:
        brain.reset()
    return "Listo, empezamos de cero."


@command("confirmar", [r"^(si|confirmo|confirmado|dale|hazlo|adelante|ok|okay|de acuerdo|claro)( por favor| hazlo)?$"],
         help="Confirma la acción pendiente.", examples=["sí"], priority=1)
def confirmar(ctx, match, texto):
    pendiente = ctx.extras.pop("pendiente", None)
    if not pendiente:
        return UNKNOWN  # sin nada pendiente, quizá le responde a Claude
    return pendiente[1]()


@command("cancelar", [r"^(no|cancela|cancelar|mejor no|olvidalo|detente)$"],
         help="Cancela la acción pendiente.", examples=["no"], priority=1)
def cancelar(ctx, match, texto):
    if not ctx.extras.pop("pendiente", None):
        return UNKNOWN
    return "Cancelado, no hice nada."
