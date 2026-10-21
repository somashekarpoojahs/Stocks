"""Technical indicators. All functions are causal: the value on a bar only uses
that bar and earlier bars, so the same code is safe for backtesting."""
import numpy as np
import pandas as pd


# ---------------------------------------------------------------- basics
def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def roc(s: pd.Series, n: int) -> pd.Series:
    return s / s.shift(n) - 1


def wilder(s: pd.Series, n: int) -> pd.Series:
    """Wilder smoothing (RMA), as used by RSI/ATR/ADX.

    Seeds with the simple mean of the first n valid values, then
    avg = (prev * (n - 1) + x) / n. NaN until the seed exists."""
    x = s.to_numpy(dtype=float)
    out = np.full(len(x), np.nan)
    run, start = 0, None
    for i in range(len(x)):
        run = run + 1 if not np.isnan(x[i]) else 0
        if run == n:
            start = i
            break
    if start is None:
        return pd.Series(out, index=s.index)
    out[start] = x[start - n + 1:start + 1].mean()
    for i in range(start + 1, len(x)):
        out[i] = out[i - 1] if np.isnan(x[i]) else (out[i - 1] * (n - 1) + x[i]) / n
    return pd.Series(out, index=s.index)


def bars_since(cond: pd.Series) -> pd.Series:
    """Number of bars since `cond` was last True (0 = true on this bar)."""
    c = cond.fillna(False).to_numpy(dtype=bool)
    out = np.full(len(c), np.nan)
    last = None
    for i, v in enumerate(c):
        if v:
            last = i
        if last is not None:
            out[i] = i - last
    return pd.Series(out, index=cond.index)


def rolling_any(cond: pd.Series, n: int) -> pd.Series:
    return cond.fillna(False).astype(float).rolling(n, min_periods=1).max() > 0


def rolling_percentile(s: pd.Series, n: int) -> pd.Series:
    """Percentile (0-1) of the latest value within the last n values."""
    def pct(x):
        return np.nan if np.isnan(x[-1]) else float(np.nanmean(x <= x[-1]))
    return s.rolling(n, min_periods=max(10, n // 2)).apply(pct, raw=True)


# ---------------------------------------------------------------- momentum
def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    au = wilder(d.clip(lower=0), n)
    ad = wilder((-d).clip(lower=0), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = 100 - 100 / (1 + au / ad)
    r = r.where(~((ad == 0) & (au > 0)), 100.0)
    r = r.where(~((ad == 0) & (au == 0)), 50.0)
    return r.where(au.notna() & ad.notna())


def macd(close: pd.Series, fast=12, slow=26, signal=9):
    line = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    sig = line.ewm(span=signal, adjust=False).mean()
    hist = line - sig
    warm = slow + signal
    mask = pd.Series(np.arange(len(close)) >= warm, index=close.index)
    return line.where(mask), sig.where(mask), hist.where(mask)


def rs_raw(close: pd.Series) -> pd.Series:
    """IBD-style weighted 12-month performance (recent quarter counts double).
    Uses whatever periods are available for shorter histories."""
    terms = [(0.4, roc(close, 63)), (0.2, roc(close, 126)),
             (0.2, roc(close, 189)), (0.2, roc(close, 252))]
    num = sum(w * r.fillna(0.0) for w, r in terms)
    den = sum(w * r.notna().astype(float) for w, r in terms)
    return num / den.replace(0, np.nan)


# ---------------------------------------------------------------- volatility / trend
def true_range(df: pd.DataFrame) -> pd.Series:
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()],
                   axis=1).max(axis=1)
    tr.iloc[0] = df["high"].iloc[0] - df["low"].iloc[0]
    return tr


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return wilder(true_range(df), n)


def adx(df: pd.DataFrame, n: int = 14):
    up = df["high"].diff()
    dn = -df["low"].diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    pdm.iloc[0] = mdm.iloc[0] = np.nan
    tr = true_range(df)
    tr.iloc[0] = np.nan
    atr_ = wilder(tr, n)
    with np.errstate(divide="ignore", invalid="ignore"):
        pdi = 100 * wilder(pdm, n) / atr_
        mdi = 100 * wilder(mdm, n) / atr_
        dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    dx = dx.replace([np.inf, -np.inf], np.nan)
    return wilder(dx, n), pdi, mdi


def supertrend(df: pd.DataFrame, period: int = 10, mult: float = 3.0):
    """Returns (line, direction). direction: +1 up, -1 down, 0 = not enough data.
    The line is the trailing stop: below price in an uptrend, above in a downtrend."""
    a = atr(df, period).to_numpy()
    h, l, c = (df[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
    n = len(c)
    upper, lower = np.full(n, np.nan), np.full(n, np.nan)
    line, direction = np.full(n, np.nan), np.zeros(n)
    started = False
    for i in range(n):
        if np.isnan(a[i]):
            continue
        hl2 = (h[i] + l[i]) / 2
        bu, bl = hl2 + mult * a[i], hl2 - mult * a[i]
        if not started:
            upper[i], lower[i] = bu, bl
            direction[i] = 1 if c[i] >= hl2 else -1
            started = True
        else:
            upper[i] = bu if (bu < upper[i - 1] or c[i - 1] > upper[i - 1]) else upper[i - 1]
            lower[i] = bl if (bl > lower[i - 1] or c[i - 1] < lower[i - 1]) else lower[i - 1]
            if direction[i - 1] == 1:
                direction[i] = -1 if c[i] < lower[i] else 1
            else:
                direction[i] = 1 if c[i] > upper[i] else -1
        line[i] = lower[i] if direction[i] == 1 else upper[i]
    return pd.Series(line, index=df.index), pd.Series(direction, index=df.index)


def bollinger(close: pd.Series, n: int = 20, k: float = 2.0):
    mid = sma(close, n)
    sd = close.rolling(n, min_periods=n).std(ddof=0)
    return mid, mid + k * sd, mid - k * sd


def keltner(df: pd.DataFrame, n: int = 20, k: float = 1.5):
    mid = ema(df["close"], n)
    a = atr(df, n)
    return mid, mid + k * a, mid - k * a


# ---------------------------------------------------------------- volume
def obv(df: pd.DataFrame) -> pd.Series:
    sign = np.sign(df["close"].diff()).fillna(0.0)
    return (sign * df["volume"]).cumsum()


def cmf(df: pd.DataFrame, n: int = 20) -> pd.Series:
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    mfm = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / rng
    mfv = mfm.fillna(0.0) * df["volume"]
    return mfv.rolling(n, min_periods=n).sum() / df["volume"].rolling(n, min_periods=n).sum()


def updown_volume_ratio(df: pd.DataFrame, n: int = 50) -> pd.Series:
    d = df["close"].diff()
    up = df["volume"].where(d > 0, 0.0).rolling(n, min_periods=n).sum()
    dn = df["volume"].where(d < 0, 0.0).rolling(n, min_periods=n).sum()
    return up / dn.replace(0, np.nan)


def rvol(volume: pd.Series, n: int = 50) -> pd.Series:
    """Today's volume vs the average of the previous n days."""
    return volume / volume.rolling(n, min_periods=20).mean().shift(1)
