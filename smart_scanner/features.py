"""Builds the full per-stock feature table (one row per bar)."""
import pandas as pd

from . import indicators as I
from . import patterns as P

COLS = ["open", "high", "low", "close", "volume"]


def compute_features(df: pd.DataFrame, cfg) -> pd.DataFrame:
    df = df[COLS].astype(float).copy()
    c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
    f = df.copy()

    for n in (10, 20, 50, 150, 200):
        f[f"sma{n}"] = I.sma(c, n)
    f["ema21"] = I.ema(c, 21)
    f["rsi"] = I.rsi(c, 14)
    f["macd"], f["macd_signal"], f["macd_hist"] = I.macd(c)
    f["atr"] = I.atr(df, 14)
    f["atr_pct"] = f["atr"] / c
    f["adx"], f["pdi"], f["mdi"] = I.adx(df, 14)

    f["st_line"], f["st_dir"] = I.supertrend(df, cfg.supertrend_period, cfg.supertrend_mult)
    prev_dir = f["st_dir"].shift()
    f["st_bars_since_up"] = I.bars_since((f["st_dir"] == 1) & (prev_dir == -1))
    f["st_bars_since_dn"] = I.bars_since((f["st_dir"] == -1) & (prev_dir == 1))

    bb_mid, f["bb_up"], f["bb_lo"] = I.bollinger(c, 20, 2.0)
    _, f["kc_up"], f["kc_lo"] = I.keltner(df, 20, 1.5)
    f["bb_width"] = (f["bb_up"] - f["bb_lo"]) / bb_mid
    f["bb_width_pct"] = I.rolling_percentile(f["bb_width"], 126)
    f["squeeze_on"] = (f["bb_up"] < f["kc_up"]) & (f["bb_lo"] > f["kc_lo"])

    f["obv"] = I.obv(df)
    f["obv_up"] = f["obv"] > I.ema(f["obv"], 21)
    f["cmf"] = I.cmf(df, 20)
    f["ud_vol"] = I.updown_volume_ratio(df, 50)
    f["rvol"] = I.rvol(v, 50)
    f["dollar_vol50"] = I.sma(c * v, 50)
    f["vol10_50"] = I.sma(v, 10) / I.sma(v, 50)

    for n in (5, 21, 63, 126):
        f[f"roc{n}"] = I.roc(c, n)
    f["hi52"] = h.rolling(252, min_periods=200).max()
    f["lo52"] = l.rolling(252, min_periods=200).min()
    f["pct_from_hi52"] = c / f["hi52"] - 1
    f["ext_atr"] = (c - f["sma50"]) / f["atr"]
    f["rs_raw"] = I.rs_raw(c)
    f["day_chg"] = c.pct_change()

    f = f.join(P.candles(df))
    f = f.join(P.setups(df, f, cfg))
    f["tt7"] = P.trend_template7(f)
    f["stage"] = P.stage(f)
    return f
