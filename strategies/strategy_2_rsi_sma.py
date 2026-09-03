import pandas as pd

from .base import BaseStrategy, Signal
from .indicators import rsi, sma


class RsiSmaStrategy(BaseStrategy):
    """Estrategia 2: RSI(14) + SMA(50) como filtro de tendencia.

    Indicadores (2): RSI de 14 periodos y SMA de 50 periodos sobre el cierre.
    Compra: precio por encima de la SMA(50) (tendencia alcista) y el RSI sale
        de sobreventa cruzando por encima de 30 (pullback comprado).
    Venta: precio por debajo de la SMA(50) (tendencia bajista) y el RSI sale
        de sobrecompra cruzando por debajo de 70 (rebote vendido / short).
    """

    name = "RSI(14) + SMA(50)"
    description = (
        "Compra en pullbacks de sobreventa dentro de una tendencia alcista "
        "y vende/abre cortos en rebotes de sobrecompra dentro de una "
        "tendencia bajista, usando la SMA(50) como filtro de tendencia."
    )
    indicators = ["RSI(14)", "SMA(50)"]

    def __init__(self, rsi_period: int = 14, sma_period: int = 50,
                 oversold: float = 30, overbought: float = 70):
        self.rsi_period = rsi_period
        self.sma_period = sma_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        rsi_val = rsi(df["close"], self.rsi_period)
        trend = sma(df["close"], self.sma_period)

        rsi_prev = rsi_val.shift(1)
        rsi_cross_up = (rsi_val > self.oversold) & (rsi_prev <= self.oversold)
        rsi_cross_down = (rsi_val < self.overbought) & (rsi_prev >= self.overbought)

        uptrend = df["close"] > trend
        downtrend = df["close"] < trend

        buy = rsi_cross_up & uptrend
        sell = rsi_cross_down & downtrend

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=object)
        signals[buy] = Signal.BUY
        signals[sell] = Signal.SELL
        return signals
