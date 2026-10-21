"""Trend-start scanner: finds stocks that look like they are STARTING a strong
uptrend (not ones that already ran a long way).

Inputs: JSON of daily bars per ticker (close/high/low/volume, last 3 opens),
plus SPY closes for relative strength. Last bar may be today's unfinished bar.

Checks (each scores a point):
  1. Supertrend(10, 3) is in an UP trend
  2. ...and it flipped up within the last 10 bars (a fresh trend)
  3. Breakout: close at a new 50-day closing high within the last 3 bars
  4. Volume surge: biggest day in the last 5 bars >= 1.5x the prior 50-day average
  5. Moving averages stacked: close > SMA20 > SMA50
  6. Momentum healthy: RSI(14) between 55 and 75 (above 80 = stretched, -1)
  7. Not over-extended: close less than 20% above SMA50 (more than 40% = -1)
  8. Relative strength: beat SPY over the window
  9. Early, not mature: up less than 60% over the window (a big run already = mature)
 10. Strong candle: today's close in the top 30% of its range (+0.5)

Flags: PINNED (daily range tiny, e.g. a takeover price), MATURE (already up a lot).
"""
import json
import sys


def sma(xs, n):
    return sum(xs[-n:]) / n


def rsi(xs, n=14):
    g = [max(b - a, 0) for a, b in zip(xs[:-1], xs[1:])]
    l = [max(a - b, 0) for a, b in zip(xs[:-1], xs[1:])]
    ag, al = sum(g[:n]) / n, sum(l[:n]) / n
    for x, y in zip(g[n:], l[n:]):
        ag, al = (ag * (n - 1) + x) / n, (al * (n - 1) + y) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def supertrend(h, l, c, period=10, mult=3.0):
    """Returns (list of +1/-1 trend per bar, final stop line value)."""
    tr = [h[0] - l[0]] + [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
                          for i in range(1, len(c))]
    atr = [None] * len(c)
    atr[period - 1] = sum(tr[:period]) / period
    for i in range(period, len(c)):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    up_band = [None] * len(c)
    dn_band = [None] * len(c)
    trend = [1] * len(c)
    for i in range(period - 1, len(c)):
        hl2 = (h[i] + l[i]) / 2
        bu, bd = hl2 + mult * atr[i], hl2 - mult * atr[i]
        if i == period - 1:
            up_band[i], dn_band[i] = bu, bd
            trend[i] = 1 if c[i] > hl2 else -1
            continue
        up_band[i] = bu if (bu < up_band[i - 1] or c[i - 1] > up_band[i - 1]) else up_band[i - 1]
        dn_band[i] = bd if (bd > dn_band[i - 1] or c[i - 1] < dn_band[i - 1]) else dn_band[i - 1]
        if trend[i - 1] == 1:
            trend[i] = -1 if c[i] < dn_band[i] else 1
        else:
            trend[i] = 1 if c[i] > up_band[i] else -1
    stop = dn_band[-1] if trend[-1] == 1 else up_band[-1]
    return trend, stop, atr[-1]


def scan(sym, d, spy_close):
    c, h, l, v = d["close"], d["high"], d["low"], d["volume"]
    o3 = d["open3"]
    last = c[-1]
    trend, st_line, atr = supertrend(h, l, c)
    flip_ago = None
    for k in range(1, len(trend)):
        if trend[-k] == 1 and trend[-k - 1] == -1:
            flip_ago = k - 1
            break
    s20, s50 = sma(c, 20), sma(c, 50)
    r = rsi(c)
    prior_high = max(c[-53:-3])
    breakout = max(c[-3:]) > prior_high
    vol_base = sum(v[-55:-5]) / 50
    vol_ratio = max(v[-5:]) / vol_base if vol_base else 0
    ext50 = (last / s50 - 1) * 100
    ret = (last / c[0] - 1) * 100
    spy_ret = (spy_close[-1] / spy_close[0] - 1) * 100
    rs = ret - spy_ret
    rng = h[-1] - l[-1]
    close_loc = (last - l[-1]) / rng if rng else 0
    atr_pct = atr / last * 100
    # candle patterns on the last two bars
    o_prev, o_last = o3[-2], o3[-1]
    c_prev = c[-2]
    engulf = last > o_last and c_prev < o_prev and last >= o_prev and o_last <= c_prev
    gap_up = (o_last / c_prev - 1) * 100

    score = 0.0
    score += 1 if trend[-1] == 1 else 0
    score += 1 if (trend[-1] == 1 and flip_ago is not None and flip_ago <= 10) else 0
    score += 1 if breakout else 0
    score += 1 if vol_ratio >= 1.5 else 0
    score += 1 if last > s20 > s50 else 0
    score += 1 if 55 <= r <= 75 else (-1 if r > 80 else 0)
    score += 1 if ext50 < 20 else (-1 if ext50 > 40 else 0)
    score += 1 if rs > 0 else 0
    score += 1 if ret < 60 else 0
    score += 0.5 if close_loc >= 0.7 else 0
    flags = []
    if atr_pct < 0.8:
        flags.append("PINNED")
    if ret >= 60:
        flags.append("MATURE")
    if ext50 > 25:
        flags.append("STRETCHED")
    return {
        "sym": sym, "last": last, "score": score, "st": "UP" if trend[-1] == 1 else "DOWN",
        "flip_ago": flip_ago, "st_stop": st_line, "breakout": breakout,
        "vol_x": vol_ratio, "sma20": s20, "sma50": s50, "rsi": r, "ext50": ext50,
        "ret": ret, "rs": rs, "close_loc": close_loc, "engulf": engulf,
        "gap": gap_up, "atr_pct": atr_pct, "flags": flags,
    }


src = sys.argv[1] if len(sys.argv) > 1 else "prices_breakouts.json"
data = json.load(open(src))
spy = data.pop("SPY")["close"]
rows = sorted((scan(s, d, spy) for s, d in data.items()), key=lambda x: -x["score"])
print(f"SPY over window: {(spy[-1]/spy[0]-1)*100:+.1f}%")
print(f"{'SYM':5} {'LAST':>8} {'SCORE':>5} {'ST':>4} {'flip':>4} {'stop':>8} {'BO':>3} "
      f"{'volx':>5} {'RSI':>5} {'ext50':>6} {'60d%':>6} {'RS':>6} {'cloc':>5} {'ATR%':>5}  FLAGS")
for x in rows:
    fa = "-" if x["flip_ago"] is None else str(x["flip_ago"])
    print(f"{x['sym']:5} {x['last']:8.2f} {x['score']:5.1f} {x['st']:>4} {fa:>4} "
          f"{x['st_stop']:8.2f} {'Y' if x['breakout'] else 'n':>3} {x['vol_x']:5.1f} "
          f"{x['rsi']:5.1f} {x['ext50']:6.1f} {x['ret']:6.1f} {x['rs']:6.1f} "
          f"{x['close_loc']:5.2f} {x['atr_pct']:5.1f}  {' '.join(x['flags'])}"
          f"{' ENGULF' if x['engulf'] else ''}")
json.dump(rows, open(src.replace(".json", "_scan.json"), "w"), indent=1)
