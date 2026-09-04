"""Backtest simple, orientado a eventos, para medir rentabilidad real.

Simula un sistema long/short reversible: una señal BUY abre/mantiene largo
(cerrando el corto si lo hubiera); una señal SELL abre/mantiene corto
(cerrando el largo si lo hubiera). Aplica comisión en cada apertura y cierre
para reflejar el coste real de operar futuros.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy, Signal


def load_tradingview_csv(path: str) -> pd.DataFrame:
    """Carga un CSV exportado desde TradingView ("Export chart data").

    Acepta tanto el formato con columna "time" (epoch en segundos o ISO)
    como variantes con mayúsculas ("Open", "High", ...). Devuelve un
    DataFrame indexado por timestamp con columnas: open, high, low, close,
    volume (volume=0 si el símbolo no lo exporta, p. ej. XAUTUSD spot).
    """
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    time_col = next((c for c in ("time", "timestamp", "date") if c in df.columns), None)
    if time_col is None:
        raise ValueError(f"No se encontró columna de tiempo en {path}: {list(df.columns)}")

    if pd.api.types.is_numeric_dtype(df[time_col]):
        unit = "ms" if df[time_col].iloc[0] > 10_000_000_000 else "s"
        df["timestamp"] = pd.to_datetime(df[time_col], unit=unit)
    else:
        df["timestamp"] = pd.to_datetime(df[time_col])

    df = df.set_index("timestamp").sort_index()

    for col in ("open", "high", "low", "close"):
        if col not in df.columns:
            raise ValueError(f"Falta la columna '{col}' en {path}")

    if "volume" not in df.columns:
        df["volume"] = 0.0

    return df[["open", "high", "low", "close", "volume"]].dropna()


@dataclass
class Trade:
    side: str
    entry_time: pd.Timestamp
    entry_price: float
    exit_time: pd.Timestamp | None = None
    exit_price: float | None = None
    pnl_pct: float = 0.0


@dataclass
class BacktestResult:
    strategy_name: str
    symbol: str
    trades: list = field(default_factory=list)
    equity_curve: pd.Series = None

    @property
    def num_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        closed = [t for t in self.trades if t.exit_price is not None]
        if not closed:
            return 0.0
        wins = sum(1 for t in closed if t.pnl_pct > 0)
        return 100 * wins / len(closed)

    @property
    def total_return_pct(self) -> float:
        if self.equity_curve is None or len(self.equity_curve) == 0:
            return 0.0
        return 100 * (self.equity_curve.iloc[-1] / self.equity_curve.iloc[0] - 1)

    @property
    def max_drawdown_pct(self) -> float:
        if self.equity_curve is None or len(self.equity_curve) == 0:
            return 0.0
        running_max = self.equity_curve.cummax()
        drawdown = (self.equity_curve - running_max) / running_max
        return 100 * drawdown.min()

    @property
    def profit_factor(self) -> float:
        closed = [t for t in self.trades if t.exit_price is not None]
        gains = sum(t.pnl_pct for t in closed if t.pnl_pct > 0)
        losses = -sum(t.pnl_pct for t in closed if t.pnl_pct < 0)
        return gains / losses if losses > 0 else float("inf") if gains > 0 else 0.0


def run_backtest(strategy: BaseStrategy, df: pd.DataFrame, symbol: str = "",
                  fee_pct: float = 0.04, initial_capital: float = 1000.0) -> BacktestResult:
    """Backtest evento a evento. `fee_pct` es el % de comisión por operación
    (apertura o cierre); 0.04% es una taker fee típica de futuros."""
    signals = strategy.generate_signals(df)
    fee = fee_pct / 100

    equity = initial_capital
    equity_curve = pd.Series(index=df.index, dtype=float)
    trades: list[Trade] = []
    position = None  # Trade abierto o None

    for ts, signal in signals.items():
        price = df.loc[ts, "close"]

        if signal == Signal.BUY:
            if position is not None and position.side == "short":
                position.exit_time = ts
                position.exit_price = price
                position.pnl_pct = (position.entry_price - price) / position.entry_price * 100 - 2 * fee_pct
                equity *= 1 + position.pnl_pct / 100
                trades.append(position)
                position = None
            if position is None:
                position = Trade(side="long", entry_time=ts, entry_price=price)

        elif signal == Signal.SELL:
            if position is not None and position.side == "long":
                position.exit_time = ts
                position.exit_price = price
                position.pnl_pct = (price - position.entry_price) / position.entry_price * 100 - 2 * fee_pct
                equity *= 1 + position.pnl_pct / 100
                trades.append(position)
                position = None
            if position is None:
                position = Trade(side="short", entry_time=ts, entry_price=price)

        # marca a mercado la posición abierta para la curva de equity
        if position is not None:
            unrealized = ((price - position.entry_price) / position.entry_price * 100
                          if position.side == "long"
                          else (position.entry_price - price) / position.entry_price * 100)
            equity_curve.loc[ts] = equity * (1 + unrealized / 100)
        else:
            equity_curve.loc[ts] = equity

    result = BacktestResult(strategy_name=strategy.name, symbol=symbol, trades=trades)
    result.equity_curve = equity_curve.ffill().fillna(initial_capital)
    return result


def summarize(results: list[BacktestResult]) -> pd.DataFrame:
    rows = [{
        "Símbolo": r.symbol,
        "Estrategia": r.strategy_name,
        "Operaciones": r.num_trades,
        "Win rate %": round(r.win_rate, 1),
        "Retorno total %": round(r.total_return_pct, 2),
        "Max drawdown %": round(r.max_drawdown_pct, 2),
        "Profit factor": round(r.profit_factor, 2) if np.isfinite(r.profit_factor) else "inf",
    } for r in results]
    return pd.DataFrame(rows)
