import pandas as pd

from .base import BaseStrategy, Signal
from .indicators import crossed_above, crossed_below, macd


class MacdCrossStrategy(BaseStrategy):
    """Estrategia 4: Cruce de MACD(12,26,9) (indicador de momentum).

    Indicadores (2, integrados en el MACD): la línea MACD (EMA12-EMA26) y su
    línea de señal (EMA9 del MACD).
    Compra: la línea MACD cruza al alza la línea de señal.
    Venta: la línea MACD cruza a la baja la línea de señal.
    """

    name = "MACD Cross (12,26,9)"
    description = (
        "Estrategia de momentum basada en el cruce entre la línea MACD y su "
        "línea de señal, ideal para capturar impulsos rápidos en velas de 5 "
        "minutos."
    )
    indicators = ["MACD line (12,26)", "MACD signal (9)"]

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        macd_line, signal_line, _hist = macd(df["close"], self.fast, self.slow, self.signal)

        buy = crossed_above(macd_line, signal_line)
        sell = crossed_below(macd_line, signal_line)

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=object)
        signals[buy] = Signal.BUY
        signals[sell] = Signal.SELL
        return signals
