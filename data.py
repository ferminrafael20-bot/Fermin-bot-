"""Obtención de velas OHLCV de 5 minutos para los símbolos de futuros.

Usa ccxt (Binance USD-M Futures por defecto) cuando está disponible y hay
acceso de red; si no, genera datos sintéticos (random walk) únicamente para
poder probar las estrategias sin conexión ni claves de API.
"""

import numpy as np
import pandas as pd

TIMEFRAME = "5m"
DEFAULT_SYMBOLS = ["BTC/USDT", "XRP/USDT", "XAUT/USDT", "SOL/USDT"]


def fetch_ohlcv(symbol: str, timeframe: str = TIMEFRAME, limit: int = 500,
                 exchange_id: str = "binanceusdm") -> pd.DataFrame:
    """Descarga velas OHLCV reales de un exchange de futuros vía ccxt.

    Lanza la excepción original de ccxt si el exchange no soporta el símbolo
    o si falla la conexión; usa `generate_sample_ohlcv` como alternativa
    offline para pruebas.
    """
    import ccxt

    exchange = getattr(ccxt, exchange_id)()
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df


def generate_sample_ohlcv(periods: int = 500, start_price: float = 100.0,
                           seed: int | None = None) -> pd.DataFrame:
    """Genera velas de 5 minutos sintéticas (random walk) para demos y tests."""
    rng = np.random.default_rng(seed)
    minutes = pd.date_range(end=pd.Timestamp.utcnow().floor("5min"), periods=periods, freq="5min")

    returns = rng.normal(loc=0.0, scale=0.002, size=periods)
    close = start_price * np.cumprod(1 + returns)

    open_ = np.roll(close, 1)
    open_[0] = start_price
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.0008, periods)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.0008, periods)))
    volume = rng.uniform(10, 1000, periods)

    df = pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }, index=minutes)
    return df
