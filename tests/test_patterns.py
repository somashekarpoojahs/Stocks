import numpy as np
import pandas as pd

from smart_scanner.features import compute_features
from smart_scanner.patterns import candles
from conftest import breakdown_stock, breakout_stock, make_bars, random_walk, restart_stock


def bars(rows):
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"]).assign(volume=1e6)


def test_bullish_engulfing():
    c = candles(bars([[10, 10.2, 9.4, 9.5], [9.4, 10.6, 9.3, 10.5]]))
    assert c["bull_engulf"].iloc[1] and not c["bear_engulf"].iloc[1]


def test_bearish_engulfing():
    c = candles(bars([[10, 10.6, 9.9, 10.5], [10.6, 10.7, 9.8, 9.9]]))
    assert c["bear_engulf"].iloc[1]


def test_hammer_and_shooting_star():
    c = candles(bars([[10, 10.05, 9.0, 10.0], [10, 11.0, 9.98, 10.02]]))
    assert c["hammer"].iloc[0] and c["shooting_star"].iloc[1]


def test_inside_bar_and_strong_close():
    c = candles(bars([[10, 11, 9, 10.9], [10.2, 10.8, 9.5, 10.75]]))
    assert c["inside_bar"].iloc[1] and c["strong_close"].iloc[1]


def test_base_breakout_detected(cfg):
    f = compute_features(breakout_stock(), cfg)
    last = f.iloc[-1]
    assert last["breakout"] and last["breakout_recent"]
    assert last["pivot"] < 101 and last["base_depth"] < 0.1
    assert not f["breakout"].iloc[-30:-1].any()     # no false breakouts inside the base


def test_gap_up_detected(cfg):
    df = random_walk(120, seed=11)
    last_close = df["close"].iloc[-2]
    df.iloc[-1] = [last_close * 1.06, last_close * 1.10, last_close * 1.055, last_close * 1.095, 5e6]
    f = compute_features(df, cfg)
    assert f["gap_up"].iloc[-1]


def test_trend_template_and_stage(cfg):
    up = compute_features(make_bars(np.linspace(40, 120, 300)), cfg).iloc[-1]
    down = compute_features(make_bars(np.linspace(120, 40, 300)), cfg).iloc[-1]
    assert up["tt7"] == 7 and up["stage"] == 2
    assert down["tt7"] <= 1 and down["stage"] == 4


def test_breakdown_detected(cfg):
    f = compute_features(breakdown_stock(), cfg)
    assert f["breakdown"].iloc[-1]


def test_intraday_poke_above_pivot_does_not_hide_breakout(cfg):
    """A 1-cent poke above the old high two days earlier must not 'move' the pivot."""
    df = breakout_stock()
    base_high = df["high"].iloc[-61:-6].max()
    df.iloc[-3, df.columns.get_loc("high")] = base_high + 0.01   # pierces the pivot intraday
    last = compute_features(df, cfg).iloc[-1]
    assert last["breakout"] and last["breakout_level"] == base_high


def test_breakout_without_volume_is_unconfirmed(cfg):
    df = breakout_stock()
    df.iloc[-1, df.columns.get_loc("volume")] = df["volume"].iloc[-30:-1].mean()   # normal volume
    last = compute_features(df, cfg).iloc[-1]
    assert not last["breakout"] and last["breakout_unconfirmed"]


def test_trend_restart_after_pullback(cfg):
    """Uptrend, a real pullback, then the fast Supertrend (7, 3) flips back up with MACD
    above its signal and RSI over 50: the 'buy arrow after a correction'."""
    f = compute_features(restart_stock(), cfg)
    assert f["restart_forming"].iloc[-6]                 # mid-correction: forming, not firing
    assert not f["restart"].iloc[:-1].any()
    last = f.iloc[-1]
    assert last["restart"] and last["st7_dir"] == 1 and last["st7_bars_since_up"] == 1


def test_no_restart_in_a_downtrend(cfg):
    f = compute_features(make_bars(np.r_[np.linspace(120, 60, 260), [58, 62, 66, 70, 74]]), cfg)
    assert (f["st7_dir"].iloc[-1] == 1) and not f["restart"].any()   # flipped, but no uptrend
