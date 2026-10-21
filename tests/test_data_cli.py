import json
import sys
import types

import numpy as np
import pandas as pd

from smart_scanner.cli import main

def test_load_yahoo_with_fake_yfinance(tmp_path, monkeypatch):
    """yfinance's bulk download shape (Ticker, Price) MultiIndex -> clean frames, then cached."""
    idx = pd.bdate_range("2026-01-01", periods=5)

    def download(batch, **kw):
        cols = pd.MultiIndex.from_product([batch, ["Open", "High", "Low", "Close", "Volume"]])
        df = pd.DataFrame(np.tile(np.arange(1, 6, dtype=float)[:, None], (1, len(cols))),
                          index=idx, columns=cols)
        if "BAD" in batch:
            df[("BAD", "Close")] = np.nan            # delisted ticker: all NaN
        return df

    fake = types.SimpleNamespace(download=download)
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    from smart_scanner.data import load_yahoo
    out = load_yahoo(["AAA", "BAD", "CCC"], cache_dir=str(tmp_path), pause=0)
    assert set(out) == {"AAA", "CCC"}
    assert list(out["AAA"].columns) == ["open", "high", "low", "close", "volume"]

    def boom(*a, **k):
        raise AssertionError("second call should come from the cache")
    fake.download = boom
    assert set(load_yahoo(["AAA", "BAD", "CCC"], cache_dir=str(tmp_path), pause=0)) == {"AAA", "CCC"}


def test_cli_scan_end_to_end(tmp_path, universe, monkeypatch):
    """IBKR-shaped JSON in -> HTML + Markdown + CSV out, settings taken from env vars."""
    path = tmp_path / "bars.json"
    path.write_text(json.dumps({t: {"time": [f"{d.date()}T13:30:00Z" for d in df.index],
                                    **{k: df[k].round(4).tolist() for k in ("open", "high", "low", "close", "volume")}}
                                for t, df in universe.items()}))
    monkeypatch.setenv("SCANNER_ACCOUNT", "300")
    res = main(["scan", "--source", f"json:{path}", "--universe", "all", "--no-earnings",
                "--out", str(tmp_path / "out")])
    stamp = res.asof.date()
    html = (tmp_path / "out" / f"scan_{stamp}.html").read_text(encoding="utf-8")
    md = (tmp_path / "out" / f"scan_{stamp}.md").read_text(encoding="utf-8")
    assert "BRK" in html and "| BRK |" in md and res.regime_label.iloc[-1] in md
    assert (res.longs["risk_usd"] <= 300 * 0.02 + 1e-9).all()


def test_unfinished_bar_dropped_while_the_market_is_open():
    from smart_scanner.data import drop_unfinished_bar
    data = {"A": pd.DataFrame({"close": [1.0, 2.0]}, index=pd.to_datetime(["2026-10-20", "2026-10-21"]))}
    ny = lambda s: pd.Timestamp(s, tz="America/New_York")
    out, d = drop_unfinished_bar(data, now=pd.Timestamp("2026-10-21 16:00", tz="UTC"))   # 12:00 New York
    assert d == "2026-10-21" and len(out["A"]) == 1
    for later in ("2026-10-21 17:00", "2026-10-22 08:00"):                           # bar is complete
        out, d = drop_unfinished_bar(data, now=ny(later))
        assert d is None and len(out["A"]) == 2


def test_cli_study_supertrend_entries(tmp_path, universe):
    path = tmp_path / "bars.json"
    path.write_text(json.dumps({t: {"time": [f"{d.date()}T13:30:00Z" for d in df.index],
                                    **{k: df[k].round(4).tolist() for k in ("open", "high", "low", "close", "volume")}}
                                for t, df in universe.items()}))
    main(["study", "--source", f"json:{path}", "--universe", "all", "--entry", "restart,st7_flip",
          "--out", str(tmp_path / "r")])
    names = {f.name.rsplit("_", 1)[0] for f in (tmp_path / "r").glob("*.md")}
    assert names == {"restart_study", "st7_flip_study"}
