"""Walk-forward backtest of the scanner's own signals.

Every signal uses only data available on the signal day (all features are causal).
Entry = next day's open. Exit = stop, 2R target, or after `hold` bars, whichever
comes first. If stop and target are both touched on the same bar, the stop is
assumed to hit first (conservative). Slippage of cfg.backtest_cost_pct per side
is deducted; broker minimum fees are not (they depend on account size).

Caveat: if the universe is today's index members, results carry survivorship bias
(stocks that collapsed and were removed from the index are missing)."""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .pipeline import score_universe
from .risk import trade_plan
from .scoring import LONG_TRIGGERS, SHORT_TRIGGERS


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    summary: pd.DataFrame
    baseline_fwd20: float
    open_trades: int


def _primary_setup(row, triggers):
    best, name = 0.0, None
    for k, w in triggers.items():
        if bool(row.get(k, False)) and w > best:
            best, name = w, k
    return name


def backtest(data: dict, cfg, side: str = "long", threshold: float = 70.0,
             hold: int = 20, cooldown: int = 10, last_n_bars: int | None = None) -> BacktestResult:
    feats, bench_f, _, _, _, _ = score_universe(data, cfg)
    triggers = LONG_TRIGGERS if side == "long" else SHORT_TRIGGERS
    score_col = "long_score" if side == "long" else "short_score"
    bench_c = bench_f["close"]
    trades, open_trades, base_rets = [], 0, []

    for t, f in feats.items():
        n = len(f)
        start = 0 if last_n_bars is None else max(0, n - last_n_bars)
        o, h, l, c = (f[k].to_numpy() for k in ("open", "high", "low", "close"))
        has_trig = pd.concat([f[k].fillna(False).astype(bool) for k in triggers], axis=1).any(axis=1)
        liquid = (f["close"] >= cfg.min_price) & (f["dollar_vol50"].fillna(np.inf) >= cfg.min_dollar_volume)
        sig = ((f[score_col] >= threshold) & has_trig & liquid & ~f["pinned"].fillna(False).astype(bool)).to_numpy()

        fwd20 = f["close"].shift(-20) / f["close"] - 1
        base_rets.extend(fwd20.iloc[start:][liquid.iloc[start:]].dropna().tolist())

        last_i = -10 ** 9
        for i in np.flatnonzero(sig):
            if i < start or i - last_i < cooldown or i + 1 >= n:
                continue
            last_i = i
            row = f.iloc[i]
            plan = trade_plan(row, cfg, side)
            r_dist = abs(plan["entry"] - plan["stop"])
            entry = o[i + 1]
            if side == "long":
                stop, target = entry - r_dist, entry + 2 * r_dist
            else:
                stop, target = entry + r_dist, entry - 2 * r_dist
            exit_px, reason, end = None, None, min(i + 1 + hold, n)
            for j in range(i + 1, end):
                if side == "long":
                    if o[j] <= stop:
                        exit_px, reason = o[j], "stop"
                    elif l[j] <= stop:
                        exit_px, reason = stop, "stop"
                    elif o[j] >= target:
                        exit_px, reason = o[j], "target"
                    elif h[j] >= target:
                        exit_px, reason = target, "target"
                else:
                    if o[j] >= stop:
                        exit_px, reason = o[j], "stop"
                    elif h[j] >= stop:
                        exit_px, reason = stop, "stop"
                    elif o[j] <= target:
                        exit_px, reason = o[j], "target"
                    elif l[j] <= target:
                        exit_px, reason = target, "target"
                if reason:
                    break
            if reason is None:
                if end - (i + 1) < hold:          # data ran out before the hold period ended
                    open_trades += 1
                    continue
                exit_px, reason = c[end - 1], "time"
            pnl = (exit_px - entry) if side == "long" else (entry - exit_px)
            pnl -= cfg.backtest_cost_pct * (entry + exit_px)      # slippage, both sides
            date = f.index[i]
            b_now = bench_c.asof(date) if isinstance(f.index, pd.DatetimeIndex) else np.nan
            b_20 = bench_c.shift(-20).asof(date) if isinstance(f.index, pd.DatetimeIndex) else np.nan
            trades.append({
                "ticker": t, "date": date, "score": round(row[score_col], 1),
                "setup": _primary_setup(row, triggers), "regime": row.get("regime"),
                "entry": round(entry, 2), "stop": round(stop, 2), "target": round(target, 2),
                "exit": round(exit_px, 2), "reason": reason, "R": pnl / r_dist,
                "ret_pct": 100 * pnl / entry,
                "fwd20_pct": 100 * (c[i + 20] / c[i] - 1) if i + 20 < n else np.nan,
                "bench_fwd20_pct": 100 * (b_20 / b_now - 1) if b_now and not np.isnan(b_now) else np.nan,
            })

    tr = pd.DataFrame(trades)
    baseline = 100 * float(np.mean(base_rets)) if base_rets else np.nan
    return BacktestResult(tr, summarize(tr), baseline, open_trades)


def summarize(tr: pd.DataFrame) -> pd.DataFrame:
    if tr.empty:
        return pd.DataFrame()

    def stats(g):
        return pd.Series({
            "trades": len(g),
            "win_rate_%": round(100 * (g["R"] > 0).mean(), 1),
            "avg_R": round(g["R"].mean(), 2),
            "avg_win_R": round(g.loc[g["R"] > 0, "R"].mean(), 2) if (g["R"] > 0).any() else 0.0,
            "avg_loss_R": round(g.loc[g["R"] <= 0, "R"].mean(), 2) if (g["R"] <= 0).any() else 0.0,
            "avg_trade_%": round(g["ret_pct"].mean(), 2),
            "avg_fwd20_%": round(g["fwd20_pct"].mean(), 2),
            "bench_fwd20_%": round(g["bench_fwd20_pct"].mean(), 2),
        })

    parts = [stats(tr).rename("ALL")]
    buckets = pd.cut(tr["score"], [0, 70, 80, 101], labels=["score <70", "score 70-80", "score 80+"], right=False)
    for name, g in tr.groupby(buckets, observed=True):
        parts.append(stats(g).rename(str(name)))
    for name, g in tr.groupby("setup"):
        parts.append(stats(g).rename(f"setup: {name}"))
    for name, g in tr.groupby("regime"):
        parts.append(stats(g).rename(f"regime: {name}"))
    return pd.DataFrame(parts)
