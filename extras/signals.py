"""Technical signal scanner for an options spread system.

Rules (daily bars, last bar may be intraday):
  Trend   : close vs SMA20 / SMA50 / SMA100
  Momentum: RSI(14, Wilder), MACD(12,26,9) histogram and its slope
  Range   : ATR(14) for expected move and strike spacing

  BULLISH  : close > SMA50 > SMA100, RSI 45-70, MACD hist > 0 or rising
  BEARISH  : close < SMA50 < SMA100, RSI 30-55, MACD hist < 0 or falling
  otherwise: NO TRADE
"""
import json


def sma(xs, n):
    return sum(xs[-n:]) / n if len(xs) >= n else None


def ema_series(xs, n):
    k = 2 / (n + 1)
    out = [xs[0]]
    for x in xs[1:]:
        out.append(x * k + out[-1] * (1 - k))
    return out


def rsi(xs, n=14):
    gains, losses = [], []
    for a, b in zip(xs[:-1], xs[1:]):
        d = b - a
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag = sum(gains[:n]) / n
    al = sum(losses[:n]) / n
    for g, l in zip(gains[n:], losses[n:]):
        ag = (ag * (n - 1) + g) / n
        al = (al * (n - 1) + l) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def macd_hist(xs):
    e12, e26 = ema_series(xs, 12), ema_series(xs, 26)
    line = [a - b for a, b in zip(e12, e26)]
    sig = ema_series(line, 9)
    hist = [a - b for a, b in zip(line, sig)]
    return hist[-1], hist[-2]


def atr(close, high15, low15):
    prev = close[-16:-1]
    trs = []
    for i in range(1, 15):
        h, l, pc = high15[i], low15[i], prev[i]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs) / len(trs)


def classify(c, s50, s100, r, h, h_prev):
    rising, falling = h > h_prev, h < h_prev
    if c > s50 > s100 and 45 <= r <= 70 and (h > 0 or rising):
        return "BULLISH"
    if c < s50 < s100 and 30 <= r <= 55 and (h < 0 or falling):
        return "BEARISH"
    return "NO TRADE"


import sys
src = sys.argv[1] if len(sys.argv) > 1 else "prices.json"
data = json.load(open(src))
rows = []
for sym, d in data.items():
    c = d["close"]
    last = c[-1]
    s20, s50, s100 = sma(c, 20), sma(c, 50), sma(c, 100)
    r = rsi(c)
    h, hp = macd_hist(c)
    a = atr(c, d["high15"], d["low15"]) if "high15" in d else None
    chg20 = (last / c[-21] - 1) * 100
    rows.append({
        "sym": sym, "last": last, "sma20": s20, "sma50": s50, "sma100": s100,
        "rsi": r, "macd_hist": h, "macd_hist_prev": hp, "atr": a,
        "chg20_pct": chg20,
        "signal": classify(last, s50, s100, r, h, hp),
    })

print(f"{'SYM':5} {'LAST':>8} {'SMA20':>8} {'SMA50':>8} {'SMA100':>8} {'RSI':>5} "
      f"{'MACDh':>7} {'prev':>7} {'ATR':>6} {'20d%':>6}  SIGNAL")
for x in rows:
    a = f"{x['atr']:.2f}" if x["atr"] else "  -"
    print(f"{x['sym']:5} {x['last']:8.2f} {x['sma20']:8.2f} {x['sma50']:8.2f} "
          f"{x['sma100']:8.2f} {x['rsi']:5.1f} {x['macd_hist']:7.2f} "
          f"{x['macd_hist_prev']:7.2f} {a:>6} {x['chg20_pct']:6.1f}  {x['signal']}")

json.dump(rows, open("signals.json", "w"), indent=1)
