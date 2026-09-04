import pandas as pd
import pytest

from backtest import load_tradingview_csv, run_backtest
from strategies import EmaCrossStrategy


def test_load_tradingview_csv_epoch_seconds(tmp_path):
    csv = tmp_path / "sample.csv"
    csv.write_text(
        "time,open,high,low,close,Volume\n"
        "1700000000,100,101,99,100.5,10\n"
        "1700000300,100.5,102,100,101.5,12\n"
    )
    df = load_tradingview_csv(str(csv))
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert len(df) == 2
    assert isinstance(df.index, pd.DatetimeIndex)


def test_load_tradingview_csv_missing_volume_defaults_to_zero(tmp_path):
    csv = tmp_path / "sample.csv"
    csv.write_text(
        "time,open,high,low,close\n"
        "2024-01-01T00:00:00Z,100,101,99,100.5\n"
    )
    df = load_tradingview_csv(str(csv))
    assert (df["volume"] == 0).all()


def test_load_tradingview_csv_missing_required_column_raises(tmp_path):
    csv = tmp_path / "sample.csv"
    csv.write_text("time,open,high,close\n1700000000,100,101,100.5\n")
    with pytest.raises(ValueError):
        load_tradingview_csv(str(csv))


def test_run_backtest_produces_equity_curve_and_trades():
    from tests.test_strategies import make_flat_then_trending_ohlcv

    df = make_flat_then_trending_ohlcv(direction=1, seed=3)
    result = run_backtest(EmaCrossStrategy(), df, symbol="TEST", fee_pct=0.04, initial_capital=1000)

    assert len(result.equity_curve) == len(df)
    assert result.equity_curve.iloc[0] > 0
    assert isinstance(result.total_return_pct, float)
    assert isinstance(result.max_drawdown_pct, float)
    assert result.max_drawdown_pct <= 0
