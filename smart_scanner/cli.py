"""Command line:
    python -m smart_scanner scan --universe sp1500 --account 500
    python -m smart_scanner backtest --universe sp500 --threshold 70
    python -m smart_scanner scan --source json:my_ibkr_bars.json --universe all

Personal settings can live in environment variables instead of flags (handy for CI):
SCANNER_ACCOUNT, SCANNER_CCY_PER_USD, SCANNER_RISK, SCANNER_FEES, SCANNER_UNIVERSE.
"""
import argparse
import datetime as dt
import os

import pandas as pd

from .backtest import backtest
from .config import FEE_PLANS, Config
from .data import load, yahoo_earnings_dates
from .pipeline import run_scan
from .report import save_report
from .universe import get_universe


def attach_earnings(res, dates: dict, today=None):
    today = today or dt.date.today()
    for name in ("longs", "shorts", "watch"):
        df = getattr(res, name)
        if df is None or df.empty:
            continue
        def label(t):
            d = dates.get(t)
            if not d:
                return ""
            days = (d - today).days
            return f"{d} (in {days}d) ⚠" if 0 <= days <= 7 else str(d)
        df["earnings"] = df["ticker"].map(label)


def _env(name: str, default, cast=float):
    v = os.environ.get(name, "").strip()
    if not v:
        return default
    try:
        return cast(v)
    except ValueError:
        raise SystemExit(f"{name} must be a number, got {v!r}")


def _config(a) -> Config:
    fee_min, fee_share, fee_pct = FEE_PLANS[a.fees]
    return Config(account_size=a.account, account_ccy_per_usd=a.ccy_per_usd,
                  risk_per_trade=a.risk, top_n=a.top, min_dollar_volume=a.min_dollar_volume,
                  fee_min_usd=fee_min, fee_per_share_usd=fee_share, fee_max_pct=fee_pct)


def main(argv=None):
    p = argparse.ArgumentParser(prog="smart_scanner")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("scan", "backtest"):
        s = sub.add_parser(name)
        s.add_argument("--universe", default=_env("SCANNER_UNIVERSE", "sp1500", str),
                       help="sp500 | sp400 | sp600 | sp1500 | nasdaq100 | all | file:PATH | AAPL,MSFT")
        s.add_argument("--source", default="yahoo", help="yahoo | json:PATH | csvdir:PATH")
        s.add_argument("--period", default="2y")
        s.add_argument("--account", type=float, default=_env("SCANNER_ACCOUNT", 1000.0),
                       help="account size in its own currency")
        s.add_argument("--ccy-per-usd", type=float, default=_env("SCANNER_CCY_PER_USD", 1.0),
                       help="e.g. 0.89 for an EUR account")
        s.add_argument("--risk", type=float, default=_env("SCANNER_RISK", 0.02),
                       help="fraction of account risked per trade")
        s.add_argument("--top", type=int, default=30)
        s.add_argument("--min-dollar-volume", type=float, default=10e6)
        s.add_argument("--fees", choices=sorted(FEE_PLANS), default=_env("SCANNER_FEES", "ibkr-fixed", str),
                       help="commission model used for position sizing")
        s.add_argument("--out", default="reports")
        s.add_argument("--refresh", action="store_true", help="ignore today's download cache")
    sub.choices["scan"].add_argument("--with-backtest", action="store_true")
    sub.choices["scan"].add_argument("--no-earnings", action="store_true")
    bt = sub.choices["backtest"]
    bt.add_argument("--side", choices=["long", "short"], default="long")
    bt.add_argument("--threshold", type=float, default=70.0)
    bt.add_argument("--hold", type=int, default=20)
    bt.add_argument("--last-n-bars", type=int, default=None)
    a = p.parse_args(argv)
    if a.fees not in FEE_PLANS:
        p.error(f"--fees / SCANNER_FEES must be one of {sorted(FEE_PLANS)}")
    cfg = _config(a)

    if a.source == "yahoo":
        tickers = get_universe(a.universe)
        tickers = sorted(set(tickers) | {cfg.benchmark})
        print(f"Downloading {len(tickers)} tickers from Yahoo ({a.period})...")
    else:
        tickers = None
    data = load(a.source, tickers, a.period, refresh=a.refresh)
    if a.source != "yahoo" and a.universe not in ("all", "sp1500"):
        keep = set(get_universe(a.universe)) | {cfg.benchmark}
        data = {t: d for t, d in data.items() if t in keep}

    if a.cmd == "backtest":
        r = backtest(data, cfg, side=a.side, threshold=a.threshold, hold=a.hold,
                     last_n_bars=a.last_n_bars)
        pd.set_option("display.width", 200)
        print(r.summary.to_string())
        print(f"\nBaseline 20-day return of an average stock-day: {r.baseline_fwd20:.2f}%")
        print(f"Trades still open at the end of the data (excluded): {r.open_trades}")
        return r

    res = run_scan(data, cfg)
    newest = pd.Timestamp(res.asof).date()
    age = (dt.date.today() - newest).days
    if age > 4:
        res.warnings.append(f"Newest bar is {age} days old ({newest}). Refresh the data first.")
    if a.source == "yahoo" and not a.no_earnings:
        top = pd.concat([d["ticker"] for d in (res.longs, res.watch, res.shorts) if not d.empty]) \
            if any(not d.empty for d in (res.longs, res.watch, res.shorts)) else []
        attach_earnings(res, yahoo_earnings_dates(list(top)))
    bt_res = backtest(data, cfg) if a.with_backtest else None
    paths = save_report(res, a.out, bt_res, f"· universe {a.universe}")
    print(f"Regime: {res.regime_label.iloc[-1]} | longs {len(res.longs)} | watch {len(res.watch)} "
          f"| shorts {len(res.shorts)}")
    for w in res.warnings:
        print("WARNING:", w)
    if not res.longs.empty:
        print(res.longs[["ticker", "grade", "score", "setups", "close", "stop", "target_2r"]]
              .to_string(index=False))
    print("Report:", paths["html"])
    return res


if __name__ == "__main__":
    main()
