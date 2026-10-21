"""Exit study: entries from the scanner, different ways of getting out.

Entry rules (`entry`):
- "score": the scanner's main signals (score >= threshold with a setup trigger).
- "restart": trend restarts (the Supertrend (7, 3) flips up after a pullback in a
  long-term uptrend; see patterns.setups).
- "st7_flip": every Supertrend (7, 3) flip up with no other filter, i.e. what the
  chart's buy arrows do on their own.

Each signal is bought at the next day's open and starts with its plan's stop, so only
the exit changes between variants. Results are in R (multiples of the initial risk)
after slippage.

Control: for every signal, a random stock that was also tradeable that same day is
bought with the same exit. For "score" its stop comes from the same trade plan. For the
Supertrend entries it sits the same number of ATRs below the price as the signal's
stop, so both carry the same risk relative to their normal daily swings. "Edge" =
signal result minus control result, which removes market timing and shows how much
the stock *selection* adds.

Trades still open when the data ends are counted at the last close, so every variant
is measured on exactly the same trades."""
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .pipeline import score_universe
from .risk import restart_plan, trade_plan
from .scoring import LONG_TRIGGERS


@dataclass(frozen=True)
class Exit:
    name: str
    target_r: float | None = None    # take profit at this many R (None = no target)
    max_hold: int = 20               # bars
    trail: str | None = None         # None | "chandelier" | "ema21" | "sma50" | a Supertrend:
                                     # "supertrend" (10, 3) / "supertrend7" (7, 3): a stop order
                                     # at the line, raised daily; "supertrend7_close": sell the
                                     # next open after a daily close below the line
    half_at_r: float | None = None   # bank half the position at this many R, the rest trails


EXITS = [
    Exit("2R target, 20 days", target_r=2.0, max_hold=20),          # the scanner's current rule
    Exit("3R target, 40 days", target_r=3.0, max_hold=40),
    Exit("Stop only, 60 days", max_hold=60),
    Exit("Trail 3 ATR under highest close, 60 days", max_hold=60, trail="chandelier"),
    Exit("Trail Supertrend, 120 days", max_hold=120, trail="supertrend"),
    Exit("Close below 21-EMA, 60 days", max_hold=60, trail="ema21"),
    Exit("Close below 50-day, 120 days", max_hold=120, trail="sma50"),
    Exit("Half at 2R, rest trails Supertrend", max_hold=120, trail="supertrend", half_at_r=2.0),
]
RESTART_EXITS = [
    Exit("Trail Supertrend (7, 3), 120 days", max_hold=120, trail="supertrend7"),   # stop order at the line
    Exit("Close below Supertrend (7, 3), 120 days", max_hold=120, trail="supertrend7_close"),  # sell arrow
    Exit("Trail Supertrend (10, 3), 120 days", max_hold=120, trail="supertrend"),
    Exit("Stop only, 60 days", max_hold=60),
    Exit("2R target, 20 days", target_r=2.0, max_hold=20),
    Exit("3R target, 40 days", target_r=3.0, max_hold=40),
    Exit("Trail 3 ATR under highest close, 60 days", max_hold=60, trail="chandelier"),
    Exit("Close below 50-day, 120 days", max_hold=120, trail="sma50"),
    Exit("Half at 2R, rest trails Supertrend (7, 3)", max_hold=120, trail="supertrend7", half_at_r=2.0),
]
ENTRIES = {     # name -> (description, exits to compare, report file prefix)
    "score": ("the scanner's own signals (score ≥ {threshold:g} with a setup trigger)", EXITS, "exit_study"),
    "restart": ("trend restarts: the Supertrend (7, 3) flips up after a pullback of 8%+ (RSI(14) "
                "dipped to 40) in a stock with a rising 200-day average, within 25% of its 52-week high",
                RESTART_EXITS, "restart_study"),
    "st7_flip": ("every Supertrend (7, 3) flip up, with no other filter (the chart's buy arrows alone)",
                 RESTART_EXITS, "st7_flip_study"),
}
ST_KEYS = {          # trail -> (line, direction, the line is also an intraday stop)
    "supertrend": ("st_line", "st_dir", True),
    "supertrend7": ("st7_line", "st7_dir", True),
    "supertrend7_close": ("st7_line", "st7_dir", False),
}
PX_COLS = ("open", "high", "low", "close", "atr", "st_line", "st_dir", "st7_line", "st7_dir",
           "ema21", "sma50")


def _arrays(f: pd.DataFrame) -> dict:
    """Plain lists: much faster than numpy scalars inside the per-bar loop."""
    return {k: f[k].to_numpy(dtype=float).tolist() for k in PX_COLS}


def _armed(px: dict, ex: Exit, k: int) -> bool:
    if ex.trail in ST_KEYS:
        return px[ST_KEYS[ex.trail][1]][k] == 1
    if ex.trail in ("ema21", "sma50"):
        ma = px[ex.trail][k]
        return ma == ma and px["close"][k] >= ma
    return False


def simulate(px: dict, e: int, entry: float, r: float, ex: Exit, cost: float = 0.001):
    """One long trade entered at the open of bar e with initial risk r per share.
    Returns (R, bars_held, reason) or None. Within a bar the stop is checked before
    any target (conservative); a gap through the stop fills at the open."""
    o, h, l, c = px["open"], px["high"], px["low"], px["close"]
    n = len(c)
    if e >= n or not r > 0:
        return None
    stop0 = entry - r
    end = min(e + ex.max_hold, n)
    hi_close = -math.inf
    armed = _armed(px, ex, e - 1) if e >= 1 else False   # trailing exits arm on the signal bar
    banked = None
    exit_px = reason = None
    j = e
    for j in range(e, end):
        level = stop0
        if j > e:
            k = j - 1
            hi_close = max(hi_close, c[k])
            if ex.trail == "chandelier":
                a = px["atr"][k]
                if a == a:
                    level = max(level, hi_close - 3.0 * a)
            elif ex.trail in ST_KEYS:
                line_key, dir_key, intraday = ST_KEYS[ex.trail]
                if px[dir_key][k] == 1:
                    armed = True
                    if intraday:
                        level = max(level, px[line_key][k])
                elif armed:                       # trend flipped down at the last close
                    exit_px, reason = o[j], "trail"
                    break
            elif ex.trail in ("ema21", "sma50"):
                ma = px[ex.trail][k]
                if ma == ma:
                    if c[k] >= ma:
                        armed = True
                    elif armed:                   # closed below the average: sell next open
                        exit_px, reason = o[j], "trail"
                        break
        if o[j] <= level:
            exit_px, reason = o[j], "stop"
            break
        if l[j] <= level:
            exit_px, reason = level, "stop"
            break
        if ex.half_at_r is not None and banked is None and h[j] >= entry + ex.half_at_r * r:
            fill = max(o[j], entry + ex.half_at_r * r)
            banked = (fill - entry) / r - cost * (entry + fill) / r
        if ex.target_r is not None and h[j] >= entry + ex.target_r * r:
            exit_px, reason = max(o[j], entry + ex.target_r * r), "target"
            break
    if exit_px is None:
        exit_px = c[j]
        reason = "time" if end == e + ex.max_hold else "open"
    rest = (exit_px - entry) / r - cost * (entry + exit_px) / r
    R = rest if banked is None else 0.5 * banked + 0.5 * rest
    return R, j - e + 1, reason


def _primary_setup(row) -> str:
    best, name = 0.0, "none"
    for k, w in LONG_TRIGGERS.items():
        if bool(row.get(k, False)) and w > best:
            best, name = w, k
    return name


def _tradeable(f: pd.DataFrame, cfg) -> np.ndarray:
    return ((f["close"] >= cfg.min_price)
            & (f["dollar_vol50"].fillna(0) >= cfg.min_dollar_volume)
            & ~f["pinned"].fillna(False).astype(bool)
            & f["long_score"].notna() & f["atr"].notna() & f["rs_rating"].notna()).to_numpy()


def _risk_per_share(row, cfg, entry: str = "score") -> float:
    plan = trade_plan(row, cfg, "long") if entry == "score" else restart_plan(row, cfg)
    return plan["entry"] - plan["stop"]


def _signals(f: pd.DataFrame, entry: str, threshold: float, ok: np.ndarray) -> np.ndarray:
    if entry == "score":
        has_trig = f[list(LONG_TRIGGERS)].fillna(False).astype(bool).any(axis=1).to_numpy()
        return (f["long_score"].to_numpy() >= threshold) & has_trig & ok
    if entry == "restart":
        return f["restart"].fillna(False).astype(bool).to_numpy() & ok
    if entry == "st7_flip":
        d = f["st7_dir"]
        return ((d == 1) & (d.shift() == -1)).to_numpy() & ok
    raise ValueError(f"unknown entry rule {entry!r}; use one of {sorted(ENTRIES)}")


@dataclass
class StudyResult:
    trades: pd.DataFrame        # one row per (trade, exit, kind)
    summary: pd.DataFrame       # per exit: signals vs random control
    best: str
    window: tuple
    n_stocks: int
    threshold: float
    entry: str = "score"


def run_study(data: dict | None, cfg, threshold: float = 70.0, cooldown: int = 10,
              exits=None, seed: int = 7, cost: float | None = None, entry: str = "score",
              feats: dict | None = None) -> StudyResult:
    """`feats` (from pipeline.score_universe) can be passed in to study several entry
    rules without recomputing every indicator."""
    if entry not in ENTRIES:
        raise ValueError(f"unknown entry rule {entry!r}; use one of {sorted(ENTRIES)}")
    exits = ENTRIES[entry][1] if exits is None else exits
    cost = cfg.backtest_cost_pct if cost is None else cost
    if feats is None:
        feats = score_universe(data, cfg)[0]
    rng = np.random.default_rng(seed)
    tickers = sorted(feats)
    px = {t: _arrays(feats[t]) for t in tickers}
    ok = {t: _tradeable(feats[t], cfg) for t in tickers}
    rows = []

    def add(kind, t, i, date, row, setup, r):
        entry_px = px[t]["open"][i + 1]
        if not (r > 0 and entry_px == entry_px):
            return False
        for ex in exits:
            out = simulate(px[t], i + 1, entry_px, r, ex, cost)
            if out is not None:
                rows.append((kind, ex.name, t, date, float(row["long_score"]), setup,
                             row.get("regime"), row.get("rs_rating"), *out))
        return True

    for t in tickers:
        f = feats[t]
        n = len(f)
        sig = _signals(f, entry, threshold, ok[t])
        last = -10 ** 9
        for i in np.flatnonzero(sig):
            if i - last < cooldown or i + 1 >= n:
                continue
            last = i
            row = f.iloc[i]
            date = f.index[i]
            r = _risk_per_share(row, cfg, entry)
            setup = _primary_setup(row) if entry == "score" else entry
            if not add("signal", t, i, date, row, setup, r):
                continue
            atrs = r / row["atr"] if row["atr"] > 0 else np.nan     # the signal's stop, in ATRs
            # control: a random stock that was tradeable the same day, same exits
            for _ in range(20):
                u = tickers[rng.integers(len(tickers))]
                g = feats[u]
                k = g.index.searchsorted(date)
                if k < len(g) - 1 and g.index[k] == date and ok[u][k]:
                    grow = g.iloc[k]
                    if entry == "score":
                        ru = _risk_per_share(grow, cfg)
                    else:                                         # same risk in ATRs, same cap
                        ru = min(atrs * grow["atr"], cfg.restart_max_stop_pct * grow["close"])
                    add("random", u, k, date, grow, "random", ru)
                    break

    cols = ["kind", "exit", "ticker", "date", "score", "setup", "regime", "rs", "R", "bars", "reason"]
    tr = pd.DataFrame(rows, columns=cols)
    summ = summarize(tr, [ex.name for ex in exits])
    best = summ["avg_R"].idxmax() if not summ.empty else ""
    dates = pd.to_datetime(tr["date"]) if not tr.empty else pd.Series(dtype="datetime64[ns]")
    window = (dates.min(), dates.max()) if not tr.empty else (None, None)
    return StudyResult(tr, summ, best, window, len(feats), threshold, entry)


def _stats(x: pd.DataFrame) -> pd.Series:
    R = x["R"]
    gains, losses = R[R > 0].sum(), -R[R < 0].sum()
    return pd.Series({
        "trades": len(x),
        "win_%": 100 * (R > 0).mean(),
        "avg_R": R.mean(),
        "median_R": R.median(),
        "profit_factor": gains / losses if losses > 0 else np.inf,
        "avg_days": x["bars"].mean(),
        "R_per_20_days": R.mean() / x["bars"].mean() * 20 if x["bars"].mean() > 0 else np.nan,
        "wins_3R_plus_%": 100 * (R >= 3).mean(),
    })


def summarize(tr: pd.DataFrame, order) -> pd.DataFrame:
    if tr.empty:
        return pd.DataFrame()
    sig = tr[tr["kind"] == "signal"].groupby("exit").apply(_stats, include_groups=False)
    rnd = tr[tr["kind"] == "random"].groupby("exit")["R"].mean().rename("random_avg_R")
    out = sig.join(rnd)
    out["edge_R"] = out["avg_R"] - out["random_avg_R"]
    return out.reindex([o for o in order if o in out.index])


def breakdown(tr: pd.DataFrame, exit_name: str, by: str) -> pd.DataFrame:
    x = tr[tr["exit"] == exit_name].copy()
    if by == "year":
        x["year"] = pd.to_datetime(x["date"]).dt.year
    elif by == "score":
        x["score"] = pd.cut(x["score"], [0, 80, 90, 101], labels=["70-80", "80-90", "90+"], right=False)
    elif by == "rs":
        x["rs"] = pd.cut(x["rs"], [0, 50, 70, 85, 100], labels=["1-49", "50-69", "70-84", "85-99"],
                         right=False)
    sig = x[x["kind"] == "signal"].groupby(by, observed=True).apply(_stats, include_groups=False)
    if by in ("year", "regime"):
        sig["random_avg_R"] = x[x["kind"] == "random"].groupby(by, observed=True)["R"].mean()
        sig["edge_R"] = sig["avg_R"] - sig["random_avg_R"]
    return sig


def _fmt_table(df: pd.DataFrame, index_name: str) -> str:
    if df is None or df.empty:
        return "_No trades._\n"
    d = df.reset_index().rename(columns={"index": index_name})
    d[d.columns[0]] = d[d.columns[0]].astype(str)
    signed = {"avg_R", "median_R", "random_avg_R", "edge_R", "R_per_20_days"}
    head = "| " + " | ".join(str(c).replace("_", " ") for c in d.columns) + " |"
    lines = [head, "|" + "---|" * len(d.columns)]
    for _, r in d.iterrows():
        cells = []
        for c in d.columns:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                v = ("∞" if np.isinf(v) else "–" if np.isnan(v) else f"{v:,.0f}" if c == "trades"
                     else f"{v:+.2f}" if c in signed else f"{v:.1f}" if c.endswith("%") or c == "avg_days"
                     else f"{v:.2f}")
            cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


TITLES = {"score": "Exit study", "restart": "Trend-restart study",
          "st7_flip": "Supertrend (7, 3) flip study"}


def build_markdown(res: StudyResult, universe: str = "") -> str:
    s = res.summary
    title = TITLES.get(res.entry, "Exit study")
    if s.empty:
        return f"# {title}\n\nNo signals in this data.\n"
    scanner = res.entry == "score"
    current = s.index[0]
    cur_label = "The scanner's current exit" if scanner else "The chart's own exit"
    c = s.loc[current]
    b = s.loc[res.best]
    n_sig = int(c["trades"])
    start, end = (d.date() if d is not None else "?" for d in res.window)
    by_year = breakdown(res.trades, res.best, "year")
    pos_years = int((by_year["edge_R"] > 0).sum()) if not by_year.empty else 0
    control = ("a random stock that was tradeable the same day, with the same exit" if scanner else
               "a random stock that was tradeable the same day, with its stop the same number of ATRs "
               "below the price (at most 15%) and the same exit")
    lines = [
        f"# {title} · {pd.Timestamp.today().date()}\n",
        f"{res.n_stocks:,} stocks ({universe}), signals from {start} to {end}. Entries are "
        f"{ENTRIES[res.entry][0].format(threshold=res.threshold)}, bought at the next day's open: "
        f"{n_sig:,} trades. Results are in **R** (multiples of the initial risk) after 0.1% slippage each way. "
        f"Control: for each signal, {control}. Trades still open at the end are counted at the last close. "
        f"Caveat: today's index members only (survivorship bias flatters long results).\n",
        "## Verdict\n",
        f"- **Best exit: {res.best}.** {b['avg_R']:+.2f}R per trade, {b['win_%']:.0f}% winners, profit factor "
        f"{b['profit_factor']:.2f}, held {b['avg_days']:.0f} days on average. {cur_label} "
        f"({current}) made {c['avg_R']:+.2f}R"
        + ("." if scanner else f" vs {c['random_avg_R']:+.2f}R on random stocks ({c['edge_R']:+.2f}R edge)."),
        f"- **Does the stock picking help?** The same exit on random stocks bought the same days made "
        f"{b['random_avg_R']:+.2f}R, so the signals add **{b['edge_R']:+.2f}R per trade**. Signals beat "
        f"random stocks in {pos_years} of {len(by_year)} years.",
        f"- **Is it worth the time?** {b['R_per_20_days']:+.2f}R per 20 days a position is held, vs "
        f"{c['R_per_20_days']:+.2f}R for {cur_label.lower()}.\n",
        "## All exits\n",
        "`random avg R` = same exit on a random stock bought the same day. `edge R` = signals minus random.\n",
        _fmt_table(s, "exit"),
        f"## Best exit ({res.best}) by year\n", _fmt_table(by_year, "year"),
    ]
    if scanner:
        lines += [f"## Best exit by setup\n", _fmt_table(breakdown(res.trades, res.best, "setup"), "setup"),
                  f"## Best exit by score\n", _fmt_table(breakdown(res.trades, res.best, "score"), "score")]
    lines += [
        f"## Best exit by relative strength (RS) on the signal day\n",
        _fmt_table(breakdown(res.trades, res.best, "rs"), "RS"),
        f"## Best exit by market regime\n", _fmt_table(breakdown(res.trades, res.best, "regime"), "regime"),
        "Not financial advice. One study on past data; markets change.\n",
    ]
    return "\n".join(lines)
