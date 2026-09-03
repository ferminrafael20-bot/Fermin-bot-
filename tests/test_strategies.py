import numpy as np
import pandas as pd
import pytest

from strategies import ALL_STRATEGIES, Signal


def make_trending_ohlcv(n=300, direction=1, seed=0):
    """OHLCV sintético con una tendencia clara para poder disparar señales."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 0.15, n)
    trend = np.linspace(0, direction * 20, n)
    close = 100 + trend + noise
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) + np.abs(rng.normal(0, 0.1, n))
    low = np.minimum(open_, close) - np.abs(rng.normal(0, 0.1, n))
    volume = rng.uniform(10, 100, n)

    index = pd.date_range("2024-01-01", periods=n, freq="5min")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=index,
    )


@pytest.mark.parametrize("strategy_cls", ALL_STRATEGIES)
def test_generate_signals_returns_aligned_series(strategy_cls):
    df = make_trending_ohlcv()
    strategy = strategy_cls()
    signals = strategy.generate_signals(df)

    assert len(signals) == len(df)
    assert signals.index.equals(df.index)
    assert set(signals.unique()).issubset({Signal.BUY, Signal.SELL, Signal.HOLD})


@pytest.mark.parametrize("strategy_cls", ALL_STRATEGIES)
def test_uses_at_most_two_indicators(strategy_cls):
    assert len(strategy_cls.indicators) <= 2


@pytest.mark.parametrize("strategy_cls", ALL_STRATEGIES)
def test_metadata_targets_5m_futures(strategy_cls):
    strategy = strategy_cls()
    assert strategy.timeframe == "5m"
    assert {"BTC/USDT", "XRP/USDT", "XAUT/USDT", "SOL/USDT"} <= set(strategy.symbols)


def make_flat_then_trending_ohlcv(direction=1, flat_periods=60, trend_periods=120, seed=0):
    """Tramo plano (para que las EMAs converjan) seguido de una tendencia
    fuerte, de modo que se produzca un cruce real de EMAs tras el arranque."""
    rng = np.random.default_rng(seed)
    flat = 100 + rng.normal(0, 0.05, flat_periods)
    trend = 100 + np.linspace(0, direction * 20, trend_periods) + rng.normal(0, 0.05, trend_periods)
    close = np.concatenate([flat, trend])

    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) + np.abs(rng.normal(0, 0.05, len(close)))
    low = np.minimum(open_, close) - np.abs(rng.normal(0, 0.05, len(close)))
    volume = rng.uniform(10, 100, len(close))

    index = pd.date_range("2024-01-01", periods=len(close), freq="5min")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=index,
    )


def test_ema_cross_buys_on_strong_uptrend():
    from strategies import EmaCrossStrategy

    df = make_flat_then_trending_ohlcv(direction=1, seed=1)
    signals = EmaCrossStrategy().generate_signals(df)
    assert (signals == Signal.BUY).any()


def test_ema_cross_sells_on_strong_downtrend():
    from strategies import EmaCrossStrategy

    df = make_flat_then_trending_ohlcv(direction=-1, seed=2)
    signals = EmaCrossStrategy().generate_signals(df)
    assert (signals == Signal.SELL).any()


def test_last_signal_returns_hold_for_empty_dataframe():
    from strategies import MacdCrossStrategy

    empty_df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    assert MacdCrossStrategy().last_signal(empty_df) == Signal.HOLD
