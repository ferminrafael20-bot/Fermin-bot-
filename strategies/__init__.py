from .base import Signal, BaseStrategy
from .strategy_1_ema_cross import EmaCrossStrategy
from .strategy_2_rsi_sma import RsiSmaStrategy
from .strategy_3_bollinger_rsi import BollingerRsiStrategy
from .strategy_4_macd import MacdCrossStrategy
from .strategy_5_stochastic_ema import StochasticEmaStrategy

ALL_STRATEGIES = [
    EmaCrossStrategy,
    RsiSmaStrategy,
    BollingerRsiStrategy,
    MacdCrossStrategy,
    StochasticEmaStrategy,
]

__all__ = [
    "Signal",
    "BaseStrategy",
    "EmaCrossStrategy",
    "RsiSmaStrategy",
    "BollingerRsiStrategy",
    "MacdCrossStrategy",
    "StochasticEmaStrategy",
    "ALL_STRATEGIES",
]
