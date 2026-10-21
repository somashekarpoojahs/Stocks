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
