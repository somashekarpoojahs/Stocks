import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from smart_scanner.config import Config  # noqa: E402


def make_bars(closes, vol=1e6, spread=0.005, opens=None, start="2024-01-01"):
    c = np.asarray(closes, dtype=float)
    o = np.r_[c[0], c[:-1]] if opens is None else np.asarray(opens, dtype=float)
    h = np.maximum(o, c) * (1 + spread)
    lo = np.minimum(o, c) * (1 - spread)
    v = np.full(len(c), float(vol)) if np.isscalar(vol) else np.asarray(vol, dtype=float)
    idx = pd.bdate_range(start, periods=len(c))
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c, "volume": v}, index=idx)


def random_walk(n, seed, drift=0.0, sigma=0.015, start=100.0, vol=1e6):
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, sigma, n)
    closes = start * np.exp(np.cumsum(rets))
    opens = np.r_[start, closes[:-1]] * (1 + rng.normal(0, 0.002, n))
    df = make_bars(closes, vol=vol, opens=opens)
    wig = np.abs(rng.normal(0, 0.006, n))
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + wig)
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - wig)
    return df


def breakout_stock(n_up=200, n_base=60):
    """Steady uptrend 50 -> 100, a tight flat base (high set at the start of the
    base), then a breakout bar on 3x volume."""
    up = np.linspace(50, 100, n_up)
    base = [100.0] + [95.0 + 4.0 * ((i % 6) / 5.0) for i in range(n_base - 1)]  # 95..99
    closes = np.r_[up, base, 104.0]
    vol = np.full(len(closes), 1e6)
    vol[-1] = 3e6
    df = make_bars(closes, vol=vol)
    df.iloc[-1, df.columns.get_loc("high")] = 104.3      # close near the high
    return df


def breakdown_stock(n_up=200, n_down=60):
    up = np.linspace(60, 100, n_up)
    down = np.linspace(100, 70, n_down)
    closes = np.r_[up, down, 64.0]
    vol = np.full(len(closes), 1e6)
    vol[-1] = 3e6
    df = make_bars(closes, vol=vol)
    df.iloc[-1, df.columns.get_loc("low")] = 63.8
    return df


def restart_stock(n_up=260, rally=(87.5, 90.0, 92.5, 94.5, 96.0)):
    """Long uptrend 50 -> 100, a 14% pullback over 12 bars (RSI well under 40), then a
    sharp rally that flips the Supertrend (7, 3) back up on the 4th rally bar."""
    wiggle = 1 + 0.01 * np.sin(np.arange(n_up) * 0.9)
    up = np.linspace(50, 100, n_up) * wiggle
    down = np.linspace(up[-1], 86, 13)[1:]
    return make_bars(np.r_[up, down, list(rally)])


@pytest.fixture
def cfg():
    return Config()


@pytest.fixture
def universe():
    n = 261
    data = {f"R{i:02d}": random_walk(n, seed=i) for i in range(28)}
    data["BRK"] = breakout_stock()
    data["DWN"] = breakdown_stock()
    data["SPY"] = make_bars(np.linspace(400, 520, n) * (1 + 0.003 * np.sin(np.arange(n))), vol=5e7)
    return data
