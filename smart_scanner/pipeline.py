"""End-to-end scan: features -> RS rating -> regime -> scores -> ranked tables."""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .features import compute_features
from .risk import trade_plan
from .scoring import (RS_FULL_RANK_AT, active_setups, breadth, grade, long_components, regime,
                      rs_rating, short_components, total)


@dataclass
class ScanResult:
    feats: dict
    bench: pd.DataFrame
    regime_checks: pd.DataFrame
    regime_score: pd.Series
    regime_label: pd.Series
    longs: pd.DataFrame
    shorts: pd.DataFrame
    watch: pd.DataFrame
    skipped: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)

    @property
    def asof(self):
        return self.bench.index[-1]


def _equal_weight_bench(data: dict) -> pd.DataFrame:
    closes = pd.DataFrame({t: d["close"] / d["close"].dropna().iloc[0] for t, d in data.items()})
    idx = closes.mean(axis=1) * 100
    return pd.DataFrame({"open": idx, "high": idx, "low": idx, "close": idx,
                         "volume": 1.0}, index=idx.index)


def score_universe(data: dict, cfg):
    """Compute features + scores for every ticker. Returns (feats, bench_f, regime parts)."""
    feats, skipped = {}, {}
    for t, df in data.items():
        if t == cfg.benchmark:
            continue
        if len(df.dropna()) < cfg.min_bars:
            skipped[t] = f"only {len(df.dropna())} bars"
            continue
        feats[t] = compute_features(df.dropna(), cfg)
    if not feats:
        raise ValueError("No tickers with enough history to scan.")
    bench_df = data.get(cfg.benchmark)
    if bench_df is None:
        skipped["_benchmark"] = f"{cfg.benchmark} missing, using an equal-weight index of the universe"
        bench_df = _equal_weight_bench({t: data[t] for t in feats})
    bench_f = compute_features(bench_df.dropna(), cfg)

    rs = rs_rating(feats, bench_f["rs_raw"])
    br = breadth(feats)
    checks, rscore, rlabel, lmult, smult = regime(bench_f, br)
    for t, f in feats.items():
        r = rs[t].reindex(f.index)
        lc = long_components(f, r)
        sc = short_components(f, r)
        f["rs_rating"] = r
        f["long_raw"] = total(lc)
        f["short_raw"] = total(sc)
        for k in lc:
            f[f"L_{k}"] = lc[k]
        f["regime"] = rlabel.reindex(f.index)
        f["long_score"] = f["long_raw"] * lmult.reindex(f.index).fillna(0.95)
        f["short_score"] = f["short_raw"] * smult.reindex(f.index).fillna(0.95)
    return feats, bench_f, checks, rscore, rlabel, skipped


def run_scan(data: dict, cfg, earnings: dict | None = None) -> ScanResult:
    feats, bench_f, checks, rscore, rlabel, skipped = score_universe(data, cfg)
    earnings = earnings or {}
    longs, shorts, watch = [], [], []
    for t, f in feats.items():
        row = f.iloc[-1]
        liquid = row["close"] >= cfg.min_price and (
            np.isnan(row["dollar_vol50"]) or row["dollar_vol50"] >= cfg.min_dollar_volume)
        if not liquid:
            skipped[t] = "price/liquidity filter"
            continue
        base = {
            "ticker": t, "close": round(row["close"], 2), "day_pct": round(100 * row["day_chg"], 2),
            "rs_rating": row["rs_rating"], "rsi": round(row["rsi"], 1), "adx": round(row["adx"], 1),
            "trend_template": int(row["tt7"] + (row["rs_rating"] >= 70)),
            "stage": row["stage"], "supertrend": "up" if row["st_dir"] == 1 else "down",
            "ext_atr": round(row["ext_atr"], 1), "rvol": round(row["rvol"], 2),
            "pct_from_hi52": round(100 * row["pct_from_hi52"], 1) if not np.isnan(row["pct_from_hi52"]) else np.nan,
            "earnings": earnings.get(t, ""),
        }
        ls, ss = row["long_score"], row["short_score"]
        long_set = active_setups(row, "long")
        short_set = active_setups(row, "short")
        has_long_trigger = any(not s.startswith("candle") for s in long_set)
        has_short_trigger = any(not s.startswith("candle") for s in short_set)
        if has_long_trigger and ls >= cfg.min_long_score:
            longs.append({**base, "score": round(ls, 1), "grade": grade(ls, row, "long"),
                          "setups": "; ".join(long_set), **trade_plan(row, cfg, "long")})
        if has_short_trigger and ss >= cfg.min_short_score:
            shorts.append({**base, "score": round(ss, 1), "grade": grade(ss, row, "short"),
                           "setups": "; ".join(short_set), **trade_plan(row, cfg, "short")})
        if (not has_long_trigger and bool(row["near_pivot"]) and row["L_trend"] >= 0.7
                and row["L_momentum"] >= 0.6):
            watch.append({**base, "score": round(ls, 1), "alert_at": round(row["pivot"], 2),
                          "pct_to_pivot": round(100 * (row["pivot"] / row["close"] - 1), 1)})
    def cols_sort(rows):
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        if "grade" in df:
            df["_g"] = df["grade"].map({"A+": 0, "A": 1, "B": 2, "C": 3})
            df = df.sort_values(["_g", "score"], ascending=[True, False]).drop(columns="_g")
        else:
            df = df.sort_values("score", ascending=False)
        return df.head(cfg.top_n).reset_index(drop=True)
    longs_df, shorts_df = cols_sort(longs), cols_sort(shorts)
    warns = data_warnings(feats, cfg, skipped)
    plans = pd.concat([d for d in (longs_df, shorts_df) if not d.empty])
    if not plans.empty and (plans["fees_usd"] > 0).any():
        share = float((plans["fees_usd"] / plans["risk_budget_usd"]).median())
        if share >= 0.15:
            warns.append(f"Broker fees take about {share:.0%} of each trade's "
                         f"${plans['risk_budget_usd'].iloc[0]:.2f} risk budget at this account size, so a "
                         f"'2R' target really pays about {plans['net_rr'].median():.1f}R (see Net R:R). Sizes "
                         f"already allow for fees; tight-stop trades suffer most, so favour fewer, wider setups.")
    return ScanResult(feats, bench_f, checks, rscore, rlabel,
                      longs_df, shorts_df, cols_sort(watch), skipped, warns)


def data_warnings(feats: dict, cfg, skipped: dict | None = None) -> list:
    """Plain-language problems with today's data that change how to read the report."""
    out = []
    if skipped and "_benchmark" in skipped:
        out.append(f"No {cfg.benchmark} data, so the market check uses an average of the scanned stocks.")
    if len(feats) < RS_FULL_RANK_AT:
        out.append(f"Only {len(feats)} stocks scanned, so RS is measured against the S&P 500 "
                   f"rather than ranked against the market. Scan 100+ stocks for true RS ranks.")
    last_rvol = pd.Series({t: f["rvol"].iloc[-1] for t, f in feats.items()}).dropna()
    if len(last_rvol) >= 5 and last_rvol.median() < 0.5:
        out.append(f"Today's bar looks unfinished: the typical stock traded only "
                   f"{last_rvol.median():.0%} of its normal volume. Breakouts need volume, so "
                   f"re-run after the US close (about 21:00 Irish time) before acting.")
    last_dates = pd.Series({t: f.index[-1] for t, f in feats.items()})
    newest = last_dates.max()
    stale = sorted(last_dates[last_dates < newest].index)
    if stale:
        day = newest.date() if hasattr(newest, "date") else newest
        out.append(f"{len(stale)} stocks have no bar for {day} (halted, delisted or a data gap): "
                   f"{', '.join(stale[:10])}{' …' if len(stale) > 10 else ''}.")
    return out
