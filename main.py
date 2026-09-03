"""Demo: aplica las 5 estrategias a BTC, XRP, XAUT y SOL en velas de 5 minutos.

Uso:
    python main.py            # datos en vivo (ccxt / Binance USD-M Futures)
    python main.py --sample   # datos sintéticos offline, para probar sin red
"""

import argparse

from data import DEFAULT_SYMBOLS, fetch_ohlcv, generate_sample_ohlcv
from strategies import ALL_STRATEGIES


def run(use_sample: bool, limit: int = 500):
    for symbol in DEFAULT_SYMBOLS:
        print(f"\n=== {symbol} (5m) ===")

        if use_sample:
            df = generate_sample_ohlcv(periods=limit, seed=hash(symbol) % (2**32))
        else:
            try:
                df = fetch_ohlcv(symbol, limit=limit)
            except Exception as exc:  # red/exchange no disponible o símbolo no listado
                print(f"  No se pudieron obtener datos en vivo ({exc}); usando datos de muestra.")
                df = generate_sample_ohlcv(periods=limit, seed=hash(symbol) % (2**32))

        for strategy_cls in ALL_STRATEGIES:
            strategy = strategy_cls()
            signal = strategy.last_signal(df)
            print(f"  {strategy.name:<32} [{', '.join(strategy.indicators)}] -> {signal.value}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", action="store_true", help="usar datos sintéticos offline")
    parser.add_argument("--limit", type=int, default=500, help="número de velas de 5m a analizar")
    args = parser.parse_args()

    run(use_sample=args.sample, limit=args.limit)
