"""Candlestick patterns and chart setups (all vectorised and causal)."""
import numpy as np
import pandas as pd

from .indicators import rolling_any


def candles(df: pd.DataFrame) -> pd.DataFrame:
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    rng = h - l
    rngz = rng.replace(0, np.nan)
    body = c - o
    ab = body.abs()
    top, bot = np.maximum(o, c), np.minimum(o, c)
    upper, lower = h - top, bot - l

    out = pd.DataFrame(index=df.index)
    out["close_loc"] = ((c - l) / rngz).fillna(0.5)      # 1 = closed at the high
    out["strong_close"] = out["close_loc"] >= 0.75
    out["weak_close"] = out["close_loc"] <= 0.25

    po, pc = o.shift(), c.shift()
    out["bull_engulf"] = (c > o) & (pc < po) & (c >= po) & (o <= pc)
    out["bear_engulf"] = (c < o) & (pc > po) & (c <= po) & (o >= pc)
    out["hammer"] = (rng > 0) & (lower >= 2 * ab) & (bot >= l + 0.6 * rng)
    out["shooting_star"] = (rng > 0) & (upper >= 2 * ab) & (top <= l + 0.4 * rng)
    out["doji"] = (rng > 0) & (ab <= 0.1 * rng)
    out["inside_bar"] = (h <= h.shift()) & (l >= l.shift())
    out["nr7"] = rng <= rng.rolling(7, min_periods=7).min()
    out["marubozu_bull"] = (body > 0) & (ab >= 0.85 * rng)

    b1, o1, c1, r1 = body.shift(2), o.shift(2), c.shift(2), rng.shift(2)
    ab2, top2, bot2 = ab.shift(1), top.shift(1), bot.shift(1)
    big1 = b1.abs() >= 0.5 * r1
    small2 = ab2 <= 0.35 * b1.abs()
    out["morning_star"] = (b1 < 0) & big1 & small2 & (top2 <= c1 + 0.1 * b1.abs()) & \
        (c > o) & (c >= (o1 + c1) / 2)
    out["evening_star"] = (b1 > 0) & big1 & small2 & (bot2 >= c1 - 0.1 * b1.abs()) & \
        (c < o) & (c <= (o1 + c1) / 2)

    sc = out["strong_close"]
    out["three_white"] = (c > o) & (pc > po) & (c.shift(2) > o.shift(2)) & \
        (c > pc) & (pc > c.shift(2)) & sc & sc.shift(1, fill_value=False) & sc.shift(2, fill_value=False)
    return out


def setups(df: pd.DataFrame, f: pd.DataFrame, cfg) -> pd.DataFrame:
    """Chart setups. `f` must already hold indicator + candle columns."""
    o, h, l, c, v = (df[k] for k in ("open", "high", "low", "close", "volume"))
    out = pd.DataFrame(index=df.index)
    lb, mn = cfg.base_lookback, cfg.base_min_len

    # --- base breakout: first close above the high of a consolidation, on volume.
    # The pivot is the base high excluding the last 5 bars, so a 1-cent intraday poke
    # above it the day before doesn't "move" the pivot and hide the real breakout.
    prior_hi = h.shift(6).rolling(lb - 5, min_periods=mn).max()
    prior_lo = l.shift(1).rolling(lb, min_periods=mn).min()
    recent_hi = h.shift(1).rolling(5, min_periods=1).max()
    recent_close_hi = c.shift(1).rolling(5, min_periods=1).max()
    depth = (prior_hi - prior_lo) / prior_hi
    base_ok = (depth <= cfg.base_max_depth) & (recent_hi <= prior_hi * 1.01)  # hasn't run above it yet
    first_close_above = (c > prior_hi) & (recent_close_hi <= prior_hi)
    bo = first_close_above & base_ok & (f["rvol"] >= cfg.rvol_breakout)
    out["pivot"] = prior_hi
    out["base_depth"] = depth
    out["breakout"] = bo
    out["breakout_recent"] = rolling_any(bo, 3)
    out["breakout_level"] = prior_hi.where(bo).ffill(limit=2)   # the level it broke, kept 3 bars
    # closed above a proper base but volume didn't confirm (or today's bar is unfinished)
    out["breakout_unconfirmed"] = first_close_above & base_ok & ~bo
    out["near_pivot"] = base_ok & (c >= 0.95 * prior_hi) & (c <= prior_hi)

    # --- VCP: three 20-bar segments with shrinking ranges, volume drying up
    def seg_depth(shift):
        hh = h.shift(shift).rolling(20, min_periods=20).max()
        ll = l.shift(shift).rolling(20, min_periods=20).min()
        return (hh - ll) / hh
    d1, d2, d3 = seg_depth(40), seg_depth(20), seg_depth(0)
    hi60 = h.rolling(60, min_periods=60).max()
    out["vcp"] = (d1 > d2) & (d2 > d3) & (d3 <= 0.10) & (f["vol10_50"] < 0.85) & \
        (c >= 0.95 * hi60) & (c > f["sma50"])

    # --- pocket pivot: up-day volume beats every down-day volume of last 10 days
    down_vol = v.where(c.diff() < 0)
    max_dn10 = down_vol.shift(1).rolling(10, min_periods=1).max()
    out["pocket_pivot"] = (c > c.shift()) & (v > max_dn10) & (c > f["sma50"]) & (c > f["sma10"])

    # --- gap up on heavy volume that holds (earnings / news gap)
    gap = o / c.shift() - 1
    gup = (gap >= cfg.gap_min_pct) & (f["rvol"] >= 2.0) & (f["close_loc"] >= 0.5)
    out["gap_pct"] = gap
    out["gap_up"] = gup
    out["gap_recent"] = rolling_any(gup, 5) & (c > f["sma20"])

    # --- pullback to a rising 21-day EMA inside an established uptrend
    bull_candle = f["strong_close"] | f["bull_engulf"] | f["hammer"] | f["morning_star"]
    out["pullback"] = (c > f["sma50"]) & (f["sma50"] > f["sma200"]) & \
        (f["ema21"] > f["ema21"].shift(5)) & (l <= f["ema21"] * 1.01) & (c > f["ema21"]) & \
        f["rsi"].between(40, 60) & bull_candle

    # --- volatility squeeze firing upward (Bollinger inside Keltner, then release)
    was_on = rolling_any(f["squeeze_on"].shift(1, fill_value=False), 5)
    out["squeeze_fire"] = was_on & ~f["squeeze_on"] & (c > f["kc_up"]) & (f["macd_hist"] > 0)

    # --- fresh Supertrend flip up
    out["fresh_flip"] = (f["st_dir"] == 1) & (f["st_bars_since_up"] <= cfg.fresh_flip_bars)

    # --- bearish setups (for puts / short side)
    out["breakdown"] = (c < prior_lo) & (f["rvol"] >= cfg.rvol_breakout) & (c < f["sma50"])
    hi50 = h.shift(1).rolling(50, min_periods=30).max()
    new_hi = h > hi50
    level = hi50.where(new_hi).ffill(limit=10)
    out["failed_breakout"] = rolling_any(new_hi, 10) & (c < level * 0.98) & (c < f["sma20"])
    out["fresh_flip_down"] = (f["st_dir"] == -1) & (f["st_bars_since_dn"] <= cfg.fresh_flip_bars)
    return out


def trend_template7(f: pd.DataFrame) -> pd.Series:
    """Mark Minervini's Trend Template minus the RS criterion (added once the
    cross-sectional RS rating is known). Returns how many of 7 checks pass."""
    c = f["close"]
    conds = [
        (c > f["sma150"]) & (c > f["sma200"]),
        f["sma150"] > f["sma200"],
        f["sma200"] > f["sma200"].shift(21),           # 200-day rising for a month
        (f["sma50"] > f["sma150"]) & (f["sma50"] > f["sma200"]),
        c > f["sma50"],
        c >= 1.30 * f["lo52"],                          # 30%+ above 52-week low
        c >= 0.75 * f["hi52"],                          # within 25% of 52-week high
    ]
    return sum(x.astype(int) for x in conds)


def stage(f: pd.DataFrame) -> pd.Series:
    """Weinstein stage: 1 basing, 2 advancing, 3 topping, 4 declining."""
    slope = f["sma150"] / f["sma150"].shift(10) - 1
    prior = f["close"] / f["close"].shift(126) - 1
    s2 = (f["close"] > f["sma150"]) & (slope > 0.005)
    s4 = (f["close"] < f["sma150"]) & (slope < -0.005)
    st = np.where(s2, 2, np.where(s4, 4, np.where(prior < 0, 1, 3))).astype(float)
    return pd.Series(st, index=f.index).where(f["sma150"].notna() & f["sma150"].shift(10).notna())
