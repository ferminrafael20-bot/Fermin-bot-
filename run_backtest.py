"""Corre las 5 estrategias sobre un CSV de velas de 5m y muestra rentabilidad real.

Uso:
    python run_backtest.py datos/BTCUSDT_5m.csv --symbol BTC/USDT
    python run_backtest.py datos/*.csv   # varios símbolos a la vez
"""

import argparse
import glob

from backtest import load_tradingview_csv, run_backtest, summarize
from strategies import ALL_STRATEGIES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_paths", nargs="+", help="ruta(s) a CSV exportado de TradingView (soporta globs)")
    parser.add_argument("--symbol", default=None, help="nombre a mostrar si solo pasas un CSV")
    parser.add_argument("--fee", type=float, default=0.04, help="comisión %% por operación (apertura/cierre)")
    parser.add_argument("--capital", type=float, default=1000.0, help="capital inicial")
    args = parser.parse_args()

    paths = [p for pattern in args.csv_paths for p in (glob.glob(pattern) or [pattern])]

    all_results = []
    for path in paths:
        symbol = args.symbol or path.split("/")[-1]
        df = load_tradingview_csv(path)
        print(f"\n{symbol}: {len(df)} velas ({df.index[0]} → {df.index[-1]})")

        for strategy_cls in ALL_STRATEGIES:
            strategy = strategy_cls()
            result = run_backtest(strategy, df, symbol=symbol, fee_pct=args.fee, initial_capital=args.capital)
            all_results.append(result)

    print("\n" + summarize(all_results).to_string(index=False))


if __name__ == "__main__":
    main()
