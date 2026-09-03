import numpy as np
import pandas as pd

from strategies.indicators import (
    bollinger_bands,
    crossed_above,
    crossed_below,
    ema,
    macd,
    rsi,
    sma,
    stochastic,
)


def test_sma_matches_manual_average():
    series = pd.Series([1, 2, 3, 4, 5])
    result = sma(series, period=3)
    assert np.isnan(result.iloc[1])
    assert result.iloc[2] == 2.0
    assert result.iloc[4] == 4.0


def test_ema_reacts_faster_than_sma_to_a_jump():
    series = pd.Series([10.0] * 20 + [20.0] * 20)
    e = ema(series, period=5)
    s = sma(series, period=5)
    assert e.iloc[22] > s.iloc[22]


def test_rsi_is_bounded_between_0_and_100():
    series = pd.Series(np.cumsum(np.random.default_rng(0).normal(0, 1, 200)) + 100)
    result = rsi(series, period=14).dropna()
    assert (result >= 0).all() and (result <= 100).all()


def test_rsi_is_high_for_strictly_rising_series():
    series = pd.Series(range(1, 30), dtype=float)
    result = rsi(series, period=14)
    assert result.iloc[-1] > 90


def test_bollinger_bands_ordering():
    series = pd.Series(np.random.default_rng(1).normal(100, 5, 100))
    upper, middle, lower = bollinger_bands(series, period=20, std_dev=2)
    valid = upper.dropna().index
    assert (upper[valid] >= middle[valid]).all()
    assert (middle[valid] >= lower[valid]).all()


def test_macd_zero_when_series_flat():
    series = pd.Series([50.0] * 60)
    macd_line, signal_line, hist = macd(series)
    assert np.allclose(macd_line.dropna(), 0)
    assert np.allclose(hist.dropna(), 0)


def test_stochastic_bounded_0_100():
    rng = np.random.default_rng(2)
    close = pd.Series(np.cumsum(rng.normal(0, 1, 100)) + 100)
    df = pd.DataFrame({
        "high": close + rng.uniform(0, 2, 100),
        "low": close - rng.uniform(0, 2, 100),
        "close": close,
    })
    k, d = stochastic(df, k_period=14, d_period=3)
    assert (k.dropna() >= 0).all() and (k.dropna() <= 100).all()
    assert (d.dropna() >= 0).all() and (d.dropna() <= 100).all()


def test_crossed_above_and_below():
    a = pd.Series([1, 2, 3, 2, 1])
    b = pd.Series([2, 2, 2, 2, 2])
    assert list(crossed_above(a, b)) == [False, False, True, False, False]
    assert list(crossed_below(a, b)) == [False, False, False, False, True]
