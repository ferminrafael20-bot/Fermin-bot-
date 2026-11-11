"""Consulta las señales de las 5 estrategias de trading del repositorio.

Ejemplos: "señal de btc", "qué dice la estrategia macd en sol",
"señal de oro con datos de prueba".
"""

from alfred.core import command

SIMBOLOS = {"btc": "BTC/USDT", "bitcoin": "BTC/USDT", "xrp": "XRP/USDT",
            "ripple": "XRP/USDT", "xaut": "XAUT/USDT", "oro": "XAUT/USDT",
            "sol": "SOL/USDT", "solana": "SOL/USDT"}
ESTRATEGIAS = {"ema": "EmaCrossStrategy", "rsi": "RsiSmaStrategy",
               "bollinger": "BollingerRsiStrategy", "macd": "MacdCrossStrategy",
               "estocastico": "StochasticEmaStrategy", "stochastic": "StochasticEmaStrategy"}
TRADUCCION = {"BUY": "COMPRA", "SELL": "VENTA", "HOLD": "ESPERAR"}


@command("señal de trading",
         [r"\bsenal(es)?\b.*\b(btc|bitcoin|xrp|ripple|xaut|oro|sol|solana)\b",
          r"\bestrategia\b.*\b(btc|bitcoin|xrp|ripple|xaut|oro|sol|solana)\b"],
         help="Da la señal actual (5m) de tus estrategias para BTC, XRP, XAUT u SOL.",
         examples=["señal de btc", "qué dice la estrategia macd en sol"], priority=40)
def senal(ctx, match, texto):
    import strategies
    from data import fetch_ohlcv, generate_sample_ohlcv

    texto_n = match.string
    simbolo = SIMBOLOS[match.group(match.lastindex)]
    elegidas = [getattr(strategies, cls) for k, cls in ESTRATEGIAS.items() if k in texto_n]
    elegidas = elegidas or strategies.ALL_STRATEGIES

    nota = ""
    if "prueba" in texto_n or "muestra" in texto_n:
        df, nota = generate_sample_ohlcv(periods=500), " (datos de prueba)"
    else:
        try:
            df = fetch_ohlcv(simbolo, limit=500)
        except Exception:
            df, nota = generate_sample_ohlcv(periods=500), " (sin conexión: datos de prueba)"

    lineas = [f"{simbolo} en 5 minutos{nota}:"]
    for cls in elegidas:
        st = cls()
        valor = st.last_signal(df).value
        lineas.append(f"  • {st.name}: {TRADUCCION.get(valor, valor)}")
    return "\n".join(lineas)
