"""Cross-sectional ranking, market regime and the 0-100 setup scores."""
import numpy as np
import pandas as pd

LONG_TRIGGERS = {            # setup name -> strength (0-1)
    "breakout_recent": 1.00,
    "vcp": 0.90,
    "squeeze_fire": 0.80,
    "gap_recent": 0.80,
    "pullback": 0.75,
    "pocket_pivot": 0.60,
    "breakout_unconfirmed": 0.55,   # closed above the pivot, volume not there (yet)
    "fresh_flip": 0.50,
}
PRIMARY_LONG = {"breakout_recent", "vcp", "squeeze_fire", "gap_recent", "pullback"}
SHORT_TRIGGERS = {
    "breakdown": 1.00,
    "failed_breakout": 0.85,
    "fresh_flip_down": 0.50,
}
PRIMARY_SHORT = {"breakdown", "failed_breakout"}
WEIGHTS = {"trend": 0.30, "momentum": 0.20, "volume": 0.15, "setup": 0.20, "risk": 0.15}
BULL_CANDLES = {"bull_engulf": "bullish engulfing", "hammer": "hammer",
                "morning_star": "morning star", "three_white": "3 white soldiers"}
BEAR_CANDLES = {"bear_engulf": "bearish engulfing", "evening_star": "evening star",
                "shooting_star": "shooting star"}


RS_FULL_RANK_AT = 100     # universe size from which RS is a pure cross-sectional rank
RS_ANCHOR_SCALE = 0.12    # ~ typical spread of the weighted 12-month return across US stocks:
                          # 10 points ahead of the benchmark -> RS ~70, 25 ahead -> ~89, 25 behind -> ~11


def rs_rating(feats: dict, bench_rs: pd.Series | None = None) -> pd.DataFrame:
    """IBD-style relative strength, 1-99, per stock per date.

    Big universe: percentile rank of each stock's weighted 12-month return
    against every other stock that day (99 = stronger than 99% of them).

    Small universe (a 10-stock watchlist): a rank among a handful of names
    means little -- the best of ten weak stocks would score 99 -- so the
    rating is anchored to the benchmark instead: 50 = moving in line with
    the S&P 500, ~85 = 20 points ahead of it, ~15 = 20 points behind.
    The two blend linearly between 20 and RS_FULL_RANK_AT stocks.
    """
    raw = pd.DataFrame({t: f["rs_raw"] for t, f in feats.items()})
    ranked = raw.rank(axis=1, pct=True) * 98 + 1
    if bench_rs is None:
        return ranked.round()
    excess = raw.sub(bench_rs.reindex(raw.index), axis=0)
    anchored = (1 + 98 / (1 + np.exp(-excess / RS_ANCHOR_SCALE))).fillna(ranked)
    n = raw.notna().sum(axis=1)
    w = ((n - 20) / (RS_FULL_RANK_AT - 20)).clip(0, 1)
    return (ranked.mul(w, axis=0) + anchored.mul(1 - w, axis=0)).round()


def breadth(feats: dict) -> pd.DataFrame:
    above = pd.DataFrame({t: (f["close"] > f["sma50"]).astype(float).where(f["sma50"].notna())
                          for t, f in feats.items()})
    nh = pd.DataFrame({t: (f["high"] >= f["hi52"]).astype(float) for t, f in feats.items()})
    nl = pd.DataFrame({t: (f["low"] <= f["lo52"]).astype(float) for t, f in feats.items()})
    return pd.DataFrame({"pct_above_50": above.mean(axis=1),
                         "new_highs": nh.sum(axis=1), "new_lows": nl.sum(axis=1)})


def regime(bench: pd.DataFrame, br: pd.DataFrame):
    """Market regime per date from the benchmark trend and market breadth."""
    c = bench["close"]
    br = br.reindex(c.index)
    checks = pd.DataFrame({
        "S&P 500 above its 50-day average": c > bench["sma50"],
        "S&P 500 above its 200-day average": c > bench["sma200"],
        "200-day average rising": bench["sma200"] > bench["sma200"].shift(21),
        "Over half of stocks above their 50-day": br["pct_above_50"] > 0.5,
        "More 52-week highs than lows": br["new_highs"] > br["new_lows"],
    })
    score = checks.sum(axis=1)
    label = pd.Series(np.where(score >= 4, "RISK-ON", np.where(score >= 2, "MIXED", "RISK-OFF")),
                      index=c.index)
    long_mult = label.map({"RISK-ON": 1.0, "MIXED": 0.95, "RISK-OFF": 0.85})
    short_mult = label.map({"RISK-ON": 0.85, "MIXED": 0.95, "RISK-OFF": 1.0})
    return checks, score, label, long_mult, short_mult


def _b(x):
    return x.fillna(False).astype(float) if x.dtype == object else x.astype(float)


def long_components(f: pd.DataFrame, rs: pd.Series) -> pd.DataFrame:
    tt8 = f["tt7"] + (rs >= 70).astype(int)
    trend = (0.60 * tt8 / 8 + 0.15 * _b(f["st_dir"] == 1)
             + 0.10 * _b((f["adx"] >= 20) & (f["pdi"] > f["mdi"])) + 0.15 * _b(f["stage"] == 2))
    rsi_s = pd.Series(np.select([f["rsi"].between(50, 75),
                                 f["rsi"].between(45, 50) | f["rsi"].between(75, 80)], [1.0, 0.5], 0.0),
                      index=f.index)
    mom = (0.60 * (rs / 99).fillna(0) + 0.15 * rsi_s + 0.125 * _b(f["macd_hist"] > 0)
           + 0.125 * _b(f["macd_hist"] > f["macd_hist"].shift()))
    vol = (0.35 * ((f["ud_vol"] - 0.8) / 0.7).clip(0, 1).fillna(0) + 0.30 * _b(f["cmf"] > 0)
           + 0.35 * _b(f["obv_up"]))
    trig = pd.concat([_b(f[k]) * w for k, w in LONG_TRIGGERS.items()], axis=1).max(axis=1)
    candle_ok = f["strong_close"] | f["bull_engulf"] | f["hammer"] | f["morning_star"] | f["three_white"]
    setup = (trig + 0.10 * _b(candle_ok & (trig > 0))).clip(upper=1)
    risk = (1 - ((f["ext_atr"] - 3) / 4).clip(0, 1)).fillna(0) * np.where(f["rsi"] > 80, 0.5, 1.0)
    return pd.DataFrame({"trend": trend, "momentum": mom, "volume": vol, "setup": setup, "risk": risk})


def short_components(f: pd.DataFrame, rs: pd.Series) -> pd.DataFrame:
    trend = (0.40 * _b(f["stage"] == 4) + 0.20 * _b(f["st_dir"] == -1)
             + 0.20 * _b((f["adx"] >= 20) & (f["mdi"] > f["pdi"]))
             + 0.20 * _b((f["close"] < f["sma50"]) & (f["sma50"] < f["sma200"])))
    mom = (0.50 * (1 - rs / 99).fillna(0) + 0.25 * _b(f["rsi"].between(25, 50))
           + 0.25 * _b(f["macd_hist"] < 0))
    vol = 0.50 * _b(f["ud_vol"] < 0.9) + 0.50 * _b(f["cmf"] < 0)
    trig = pd.concat([_b(f[k]) * w for k, w in SHORT_TRIGGERS.items()], axis=1).max(axis=1)
    bear_candle = f["bear_engulf"] | f["evening_star"] | f["shooting_star"] | f["weak_close"]
    setup = (trig + 0.10 * _b(bear_candle & (trig > 0))).clip(upper=1)
    risk = (1 - ((-f["ext_atr"] - 3) / 4).clip(0, 1)).fillna(0) * np.where(f["rsi"] < 20, 0.5, 1.0)
    return pd.DataFrame({"trend": trend, "momentum": mom, "volume": vol, "setup": setup, "risk": risk})


def total(components: pd.DataFrame) -> pd.Series:
    return 100 * sum(components[k] * w for k, w in WEIGHTS.items())


def grade(score: float, row=None, side: str = "long") -> str:
    """Score bands, but top grades also need confluence so a single lucky
    indicator can't produce an A+."""
    if row is None:
        return "A+" if score >= 80 else "A" if score >= 70 else "B" if score >= 60 else "C"
    rs = row.get("rs_rating", np.nan)
    rs = 0 if rs != rs else rs
    if side == "long":
        tt8 = row["tt7"] + (rs >= 70)
        primary = any(bool(row.get(k, False)) for k in PRIMARY_LONG)
        if score >= 80 and tt8 >= 7 and rs >= 80 and primary:
            return "A+"
        if score >= 70 and tt8 >= 5 and rs >= 60:
            return "A"
    else:
        primary = any(bool(row.get(k, False)) for k in PRIMARY_SHORT)
        if score >= 80 and row.get("stage") == 4 and rs <= 20 and primary:
            return "A+"
        if score >= 70 and rs <= 40:
            return "A"
    return "B" if score >= 60 else "C"


def active_setups(row: pd.Series, side: str = "long") -> list:
    keys = LONG_TRIGGERS if side == "long" else SHORT_TRIGGERS
    names = {"breakout_recent": "Base breakout", "vcp": "VCP (tightening)",
             "squeeze_fire": "Squeeze firing", "gap_recent": "Gap up holding",
             "pullback": "Pullback to 21-EMA", "pocket_pivot": "Pocket pivot",
             "breakout_unconfirmed": "Breakout, volume unconfirmed",
             "fresh_flip": "Supertrend flip up", "breakdown": "Breakdown",
             "failed_breakout": "Failed breakout", "fresh_flip_down": "Supertrend flip down"}
    out = [names[k] for k in keys if bool(row.get(k, False))]
    candle_names = BULL_CANDLES if side == "long" else BEAR_CANDLES
    candles = [v for k, v in candle_names.items() if bool(row.get(k, False))]
    if candles:
        out.append("candle: " + ", ".join(candles))
    return out
