"""Price data loaders: Yahoo (free, whole market), JSON (e.g. IBKR exports), CSV folders."""
import json
from pathlib import Path

import pandas as pd

COLS = ["open", "high", "low", "close", "volume"]


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=lambda c: str(c).lower().replace(" ", "_"))
    if "adj_close" in df.columns and "close" not in df.columns:
        df = df.rename(columns={"adj_close": "close"})
    df = df[[c for c in COLS if c in df.columns]]
    return df.dropna(subset=["close"]).astype(float)


def load_yahoo(tickers, period: str = "2y", chunk: int = 100, cache_dir: str = "cache",
               refresh: bool = False, pause: float = 1.0, retries: int = 3) -> dict:
    """Daily OHLCV for many tickers via yfinance, cached once per day.

    Yahoo throttles bulk downloads, so batches are spaced out and a failed batch
    is retried with a growing wait. Use refresh=True to ignore today's cache
    (e.g. a first run before the close left an unfinished bar in it)."""
    import time

    import yfinance as yf

    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    key = cache / f"yahoo_{period}_{pd.Timestamp.today().date()}_{len(tickers)}.pkl"
    if key.exists() and not refresh:
        return pd.read_pickle(key)
    out, failed = {}, []
    for i in range(0, len(tickers), chunk):
        batch = list(tickers[i:i + chunk])
        raw = None
        for attempt in range(retries):
            try:
                raw = yf.download(batch, period=period, interval="1d", auto_adjust=True,
                                  group_by="ticker", threads=True, progress=False)
            except Exception as e:  # noqa: BLE001 - rate limits / network blips
                print(f"  batch {i // chunk + 1}: {type(e).__name__}, retrying...")
                raw = None
            if raw is not None and not raw.empty:
                break
            time.sleep(5 * (attempt + 1))
        if raw is None or raw.empty:
            failed.extend(batch)
            continue
        for t in batch:
            try:
                df = raw[t] if isinstance(raw.columns, pd.MultiIndex) else raw
            except KeyError:
                failed.append(t)
                continue
            df = _normalize(df)
            if len(df):
                out[t] = df
        time.sleep(pause)
    if failed:
        print(f"  no data for {len(failed)} tickers (delisted, renamed or throttled): "
              f"{', '.join(failed[:15])}{' ...' if len(failed) > 15 else ''}")
    if out:
        pd.to_pickle(out, key)
    return out


def yahoo_earnings_dates(tickers) -> dict:
    """Next earnings date per ticker (best effort; Yahoo's calendar can be missing)."""
    import yfinance as yf

    out = {}
    for t in tickers:
        try:
            cal = yf.Ticker(t).calendar
            d = None
            if isinstance(cal, dict):
                v = cal.get("Earnings Date")
                d = v[0] if isinstance(v, (list, tuple)) and v else v
            elif cal is not None and hasattr(cal, "loc") and "Earnings Date" in cal.index:
                d = cal.loc["Earnings Date"].iloc[0]
            if d is not None:
                out[t] = pd.Timestamp(d).date()
        except Exception:  # noqa: BLE001 - one bad ticker must not stop the scan
            continue
    return out


def load_json(path: str) -> dict:
    """{"TICKER": {"date": [...], "open": [...], "high": [...], "low": [...],
    "close": [...], "volume": [...]}} -> {ticker: DataFrame}.

    Also accepts IBKR's price-history shape as-is ("time" holding ISO
    timestamps such as "2026-10-20T13:30:00Z" instead of "date")."""
    raw = json.loads(Path(path).read_text())
    out = {}
    for t, d in raw.items():
        dates = d.get("date") or [str(x)[:10] for x in d.get("time", [])] or None
        idx = pd.to_datetime(dates) if dates else None
        out[t.upper()] = pd.DataFrame({k: d[k] for k in COLS}, index=idx).astype(float)
    return out


def load_csv_dir(path: str) -> dict:
    """One CSV per ticker (file name = ticker) with Date, Open, High, Low, Close, Volume."""
    out = {}
    for p in sorted(Path(path).glob("*.csv")):
        df = pd.read_csv(p, index_col=0, parse_dates=True)
        out[p.stem.upper()] = _normalize(df)
    return out


def load(source: str, tickers=None, period: str = "2y", refresh: bool = False) -> dict:
    if source == "yahoo":
        return load_yahoo(tickers, period, refresh=refresh)
    if source.startswith("json:"):
        return load_json(source[5:])
    if source.startswith("csvdir:"):
        return load_csv_dir(source[7:])
    raise ValueError(f"Unknown source {source!r}")
