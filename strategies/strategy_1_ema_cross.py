import pandas as pd

from .base import BaseStrategy, Signal
from .indicators import crossed_above, crossed_below, ema


class EmaCrossStrategy(BaseStrategy):
    """Estrategia 1: Cruce de Medias Móviles Exponenciales (EMA 9 / EMA 21).

    Indicadores (2): EMA rápida (9) y EMA lenta (21) sobre el precio de cierre.
    Compra: la EMA rápida cruza al alza a la EMA lenta (momentum alcista).
    Venta: la EMA rápida cruza a la baja a la EMA lenta (momentum bajista).
    """

    name = "EMA Cross (9/21)"
    description = (
        "Sigue tendencia de corto plazo cruzando una EMA rápida de 9 periodos "
        "con una EMA lenta de 21 periodos en velas de 5 minutos."
    )
    indicators = ["EMA(9)", "EMA(21)"]

    def __init__(self, fast_period: int = 9, slow_period: int = 21):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ema_fast = ema(df["close"], self.fast_period)
        ema_slow = ema(df["close"], self.slow_period)

        buy = crossed_above(ema_fast, ema_slow)
        sell = crossed_below(ema_fast, ema_slow)

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=object)
        signals[buy] = Signal.BUY
        signals[sell] = Signal.SELL
        return signals
