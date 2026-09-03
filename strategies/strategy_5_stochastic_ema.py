import pandas as pd

from .base import BaseStrategy, Signal
from .indicators import crossed_above, crossed_below, ema, stochastic


class StochasticEmaStrategy(BaseStrategy):
    """Estrategia 5: Oscilador Estocástico(14,3) + EMA(50) como filtro de tendencia.

    Indicadores (2): Estocástico %K/%D y EMA de 50 periodos.
    Compra: %K cruza al alza a %D en zona de sobreventa (< 20) y el precio
        está por encima de la EMA(50).
    Venta: %K cruza a la baja a %D en zona de sobrecompra (> 80) y el precio
        está por debajo de la EMA(50).
    """

    name = "Stochastic(14,3) + EMA(50)"
    description = (
        "Combina el oscilador estocástico para detectar giros en zonas "
        "extremas con una EMA(50) que filtra la operativa a favor de la "
        "tendencia dominante."
    )
    indicators = ["Stochastic %K/%D(14,3)", "EMA(50)"]

    def __init__(self, k_period: int = 14, d_period: int = 3, ema_period: int = 50,
                 oversold: float = 20, overbought: float = 80):
        self.k_period = k_period
        self.d_period = d_period
        self.ema_period = ema_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        percent_k, percent_d = stochastic(df, self.k_period, self.d_period)
        trend = ema(df["close"], self.ema_period)

        cross_up = crossed_above(percent_k, percent_d)
        cross_down = crossed_below(percent_k, percent_d)

        buy = cross_up & (percent_k < self.oversold) & (df["close"] > trend)
        sell = cross_down & (percent_k > self.overbought) & (df["close"] < trend)

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=object)
        signals[buy] = Signal.BUY
        signals[sell] = Signal.SELL
        return signals
