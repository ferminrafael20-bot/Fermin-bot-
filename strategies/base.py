from enum import Enum

import pandas as pd

#: Futures perpetuos soportados por el bot (símbolos estilo ccxt).
DEFAULT_SYMBOLS = ["BTC/USDT", "XRP/USDT", "XAUT/USDT", "SOL/USDT"]

#: Todas las estrategias de este proyecto operan en velas de 5 minutos.
TIMEFRAME = "5m"


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class BaseStrategy:
    """Interfaz común para las estrategias de trading en futuros a 5 minutos."""

    name: str = "BaseStrategy"
    description: str = ""
    indicators: list[str] = []
    timeframe: str = TIMEFRAME
    symbols: list[str] = DEFAULT_SYMBOLS

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Devuelve una Series de `Signal` alineada al índice de `df`.

        `df` debe tener columnas: open, high, low, close, volume, ordenadas
        cronológicamente (vela más antigua primero).
        """
        raise NotImplementedError

    def last_signal(self, df: pd.DataFrame) -> Signal:
        signals = self.generate_signals(df)
        return signals.iloc[-1] if len(signals) else Signal.HOLD
