import pandas as pd

from .base import BaseStrategy, Signal
from .indicators import bollinger_bands, rsi


class BollingerRsiStrategy(BaseStrategy):
    """Estrategia 3: Bandas de Bollinger(20,2) + RSI(14) (reversión a la media).

    Indicadores (2): Bandas de Bollinger de 20 periodos / 2 desviaciones y
    RSI de 14 periodos.
    Compra: el cierre toca o perfora la banda inferior y el RSI está en
        sobreventa (< 30) -> posible rebote alcista.
    Venta: el cierre toca o perfora la banda superior y el RSI está en
        sobrecompra (> 70) -> posible corrección bajista / short.
    """

    name = "Bollinger Bands(20,2) + RSI(14)"
    description = (
        "Estrategia de reversión a la media: busca compras cuando el precio "
        "se sobreextiende por debajo de la banda inferior con RSI en "
        "sobreventa, y ventas cuando se sobreextiende por encima de la "
        "banda superior con RSI en sobrecompra."
    )
    indicators = ["Bollinger Bands(20,2)", "RSI(14)"]

    def __init__(self, bb_period: int = 20, bb_std: float = 2.0,
                 rsi_period: int = 14, oversold: float = 30, overbought: float = 70):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        upper, _middle, lower = bollinger_bands(df["close"], self.bb_period, self.bb_std)
        rsi_val = rsi(df["close"], self.rsi_period)

        buy = (df["close"] <= lower) & (rsi_val < self.oversold)
        sell = (df["close"] >= upper) & (rsi_val > self.overbought)

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=object)
        signals[buy] = Signal.BUY
        signals[sell] = Signal.SELL
        return signals
