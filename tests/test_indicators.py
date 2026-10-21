import numpy as np
import pandas as pd
import pytest

from smart_scanner import indicators as I
from conftest import make_bars, random_walk

# Wilder RSI worked example published by StockCharts (first RSI = 70.53, then 66.32)
STOCKCHARTS = [44.3389, 44.0902, 44.1497, 43.6124, 44.3278, 44.8264, 45.0955, 45.4245, 45.8433,
               46.0826, 45.8931, 46.0328, 45.6140, 46.2820, 46.2820, 46.0028, 46.0328, 46.4116]


def ref_rsi(xs, n=14):
    """Plain-loop Wilder RSI used as an independent reference."""
    g = [max(b - a, 0) for a, b in zip(xs[:-1], xs[1:])]
    l = [max(a - b, 0) for a, b in zip(xs[:-1], xs[1:])]
    ag, al = sum(g[:n]) / n, sum(l[:n]) / n
    for x, y in zip(g[n:], l[n:]):
        ag, al = (ag * (n - 1) + x) / n, (al * (n - 1) + y) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def test_rsi_matches_published_example():
    r = I.rsi(pd.Series(STOCKCHARTS))
    assert r.iloc[13] != r.iloc[13]          # NaN before 14 changes exist
    assert r.iloc[14] == pytest.approx(70.53, abs=0.05)
    assert r.iloc[15] == pytest.approx(66.32, abs=0.05)


def test_rsi_matches_reference_loop():
    s = random_walk(300, seed=7)["close"]
    assert I.rsi(s).iloc[-1] == pytest.approx(ref_rsi(list(s)), abs=1e-9)


def test_rsi_extremes():
    assert I.rsi(pd.Series(np.arange(1, 40, dtype=float))).iloc[-1] == 100
    assert I.rsi(pd.Series(np.arange(40, 1, -1, dtype=float))).iloc[-1] == pytest.approx(0)
    assert I.rsi(pd.Series(np.full(40, 5.0))).iloc[-1] == 50


def test_atr_constant_range():
    df = pd.DataFrame({"open": 10.0, "high": 11.0, "low": 9.0, "close": 10.0, "volume": 1.0},
                      index=range(50))
    assert I.atr(df, 14).iloc[-1] == pytest.approx(2.0)


def test_supertrend_flips_down_after_crash():
    closes = np.r_[np.linspace(50, 100, 80), np.linspace(100, 60, 30)]
    df = make_bars(closes)
    line, d = I.supertrend(df, 10, 3)
    assert d.iloc[79] == 1 and line.iloc[79] < df["close"].iloc[79]
    assert d.iloc[-1] == -1 and line.iloc[-1] > df["close"].iloc[-1]


def test_adx_strong_trend():
    df = random_walk(200, seed=3, drift=0.006, sigma=0.008)
    a, pdi, mdi = I.adx(df, 14)
    assert a.iloc[-1] > 25 and pdi.iloc[-1] > mdi.iloc[-1]


def test_macd_positive_in_uptrend():
    _, _, hist = I.macd(pd.Series(np.exp(np.linspace(0, 1, 120)) * 100))
    line, _, _ = I.macd(pd.Series(np.exp(np.linspace(0, 1, 120)) * 100))
    assert line.iloc[-1] > 0 and hist.iloc[:30].isna().all()


def test_bars_since():
    s = pd.Series([False, True, False, False, True, False])
    assert I.bars_since(s).tolist()[1:] == [0, 1, 2, 0, 1]
    assert np.isnan(I.bars_since(s).iloc[0])


def test_volume_indicators():
    df = make_bars(np.arange(100, 160, dtype=float))
    df["high"] = df["close"]                     # every bar closes at its high
    assert I.obv(df).is_monotonic_increasing
    assert I.cmf(df, 20).iloc[-1] == pytest.approx(1.0)
    assert np.isinf(I.updown_volume_ratio(df, 50).iloc[-1]) or \
        np.isnan(I.updown_volume_ratio(df, 50).iloc[-1])   # no down days at all


def test_rs_raw_uses_available_periods():
    s = pd.Series(np.linspace(100, 200, 100))   # < 126 bars: only the 63-day term exists
    assert I.rs_raw(s).iloc[-1] == pytest.approx(s.iloc[-1] / s.iloc[-64] - 1)
